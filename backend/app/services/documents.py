"""Persist document jobs, then atomically publish chunks and retire the upload."""

import asyncio
import hashlib
import logging
from threading import Event, Thread
from uuid import uuid4

from sqlalchemy import Float, Text, bindparam, func, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.integrations.ai import AIError, OpenAIProvider
from app.integrations import pdf
from app.models.documents import chunk, document, upload
from app.models.vector import Vector1536
from app.services.metadata import MetadataError

logger = logging.getLogger(__name__)
INDEX_FORMAT = ":pdf-page-v1"
PUBLIC = (document.c.id, document.c.name, document.c.status, document.c.error, document.c.created_at)


def available(settings):
    return (settings.documents_enabled and settings.ai_enabled
            and bool(settings.openai_api_key.get_secret_value().strip())
            and settings.ai_embedding_dimensions == 1536)


def list_documents(engine, limit, offset):
    with engine.connect() as connection:
        return [dict(row) for row in connection.execute(
            select(*PUBLIC).order_by(document.c.created_at.desc(), document.c.id).limit(limit).offset(offset),
        ).mappings()]


def create(engine, name, data):
    identity = uuid4()
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(180018, 4)"))
        pending = connection.scalar(select(func.count()).select_from(upload))
        if pending >= 5:
            raise MetadataError("document_queue_full", "Hay cinco PDF en espera de procesamiento.", 429)
        row = connection.execute(document.insert().values(
            id=identity, name=name, sha256=hashlib.sha256(data).hexdigest(), status="pending",
        ).returning(*PUBLIC)).mappings().one()
        connection.execute(upload.insert().values(document_id=identity, pdf=data))
        return dict(row)


def delete(engine, identity):
    with engine.begin() as connection:
        if connection.scalar(document.delete().where(document.c.id == identity).returning(document.c.id)) is None:
            raise MetadataError("document_not_found", "No existe ese documento.", 404)


def claim(engine):
    with engine.begin() as connection:
        identity = connection.scalar(select(document.c.id).where(document.c.status == "pending")
                                     .order_by(document.c.created_at, document.c.id).limit(1).with_for_update())
        if identity is None:
            return None
        attempt = uuid4()
        connection.execute(document.update().where(document.c.id == identity)
                           .values(status="processing", attempt=attempt))
        return identity, attempt


def complete(engine, identity, attempt, *, rows=None, model_key=None, error=None):
    with engine.begin() as connection:
        updated = connection.scalar(document.update().where(
            document.c.id == identity, document.c.attempt == attempt, document.c.status == "processing",
        ).values(status="ready" if rows else "failed", model_key=model_key, error=error,
                 attempt=None).returning(document.c.id))
        if updated is None:
            return
        if rows:
            connection.execute(chunk.insert(), rows)
        connection.execute(upload.delete().where(upload.c.document_id == identity))


async def encode(provider, content):
    result = await provider.embed(content)
    try:
        if result["model_key"] != provider.model_key:
            raise ValueError
        vector = result["vector"]
        Vector1536().bind_processor(None)(vector)
    except (KeyError, TypeError, ValueError):
        raise AIError("ai_invalid_response") from None
    return vector


async def embed_pages(provider, identity, sections, should_stop):
    rows = []
    for piece in sections:
        if should_stop():
            raise InterruptedError
        vector = await encode(provider, piece["content"])
        rows.append(dict(piece, id=uuid4(), document_id=identity, embedding=vector))
    return rows


class DocumentWorker:
    def __init__(self, engine, settings, provider_factory=OpenAIProvider):
        self.engine = engine
        self.settings = settings
        self.provider_factory = provider_factory
        self.stop_event = Event()
        self.thread = Thread(target=self.run, name="echobeats-documents", daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=5)

    def run(self):
        while not self.stop_event.is_set():
            try:
                with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as owner:
                    if owner.scalar(text("SELECT pg_try_advisory_lock(180018, 3)")):
                        try:
                            with self.engine.begin() as connection:
                                connection.execute(document.update().where(document.c.status == "processing")
                                                   .values(status="pending", attempt=None))
                            while not self.stop_event.is_set():
                                owner.execute(text("SELECT 1"))
                                job = claim(self.engine)
                                if job:
                                    self.process(*job)
                                else:
                                    self.stop_event.wait(2)
                        finally:
                            if not owner.invalidated:
                                owner.execute(text("SELECT pg_advisory_unlock(180018, 3)"))
            except SQLAlchemyError:
                logger.warning("La cola documental no está disponible temporalmente.")
            self.stop_event.wait(2)

    def process(self, identity, attempt):
        try:
            with self.engine.connect() as connection:
                original = connection.scalar(select(upload.c.pdf).where(upload.c.document_id == identity))
            if original is None:
                complete(self.engine, identity, attempt, error="missing_upload")
                return
            sections = pdf.extract(original, self.stop_event)
            def should_stop():
                if self.stop_event.is_set():
                    return True
                with self.engine.connect() as connection:
                    return connection.scalar(select(document.c.attempt).where(document.c.id == identity)) != attempt

            provider = self.provider_factory(self.settings)
            rows = asyncio.run(embed_pages(provider, identity, sections, should_stop))
            complete(self.engine, identity, attempt, rows=rows, model_key=provider.model_key + INDEX_FORMAT)
        except InterruptedError:
            return
        except (pdf.DocumentError, AIError) as exc:
            reason = exc.code if isinstance(exc, AIError) else str(exc)
            complete(self.engine, identity, attempt, error=reason)
        except OSError:
            complete(self.engine, identity, attempt, error="processing_failed")


def ready_document(connection, identity, model_key):
    row = connection.execute(select(document.c.name, document.c.status, document.c.model_key)
                             .where(document.c.id == identity)).one_or_none()
    if row is None:
        raise MetadataError("document_not_found", "No existe ese documento.", 404)
    if row.status != "ready" or row.model_key != model_key:
        raise MetadataError("document_not_ready", "El documento necesita un índice vigente para consultarlo.", 409)
    return row.name


def retrieve(engine, identity, model_key, question, vector):
    with engine.connect() as connection:
        name = ready_document(connection, identity, model_key)
        distance = chunk.c.embedding.op("<=>", return_type=Float)(vector)
        lexical = func.ts_rank_cd(func.to_tsvector("simple", chunk.c.content),
                                  func.plainto_tsquery("simple", bindparam("question", question, type_=Text)))
        base = select(chunk.c.id, chunk.c.page, chunk.c.section, chunk.c.content).where(chunk.c.document_id == identity)
        semantic = connection.execute(base.order_by(distance, chunk.c.page, chunk.c.ordinal).limit(12)).all()
        textual = connection.execute(base.where(lexical > 0)
                                     .order_by(lexical.desc(), chunk.c.page, chunk.c.ordinal).limit(12)).all()
        ranks = {}
        for results in (semantic, textual):
            for rank, row in enumerate(results, 1):
                ranks[row] = ranks.get(row, 0) + 1 / (60 + rank)
        return name, sorted(ranks, key=ranks.get, reverse=True)[:4]


async def answer(engine, provider, identity, question):
    from starlette.concurrency import run_in_threadpool

    def verify():
        with engine.connect() as connection:
            ready_document(connection, identity, provider.model_key + INDEX_FORMAT)

    await run_in_threadpool(verify)
    vector = await encode(provider, question)
    name, rows = await run_in_threadpool(retrieve, engine, identity, provider.model_key + INDEX_FORMAT, question, vector)
    if not rows:
        return {"answer": None, "sources": []}
    evidence = [{"source_id": str(row.id), "version": 1, "text": row.content} for row in rows]
    try:
        output = (await provider.generate(question, evidence))["output"]
        citations = output["evidence"]
    except AIError:
        citations = []
    await run_in_threadpool(verify)
    references = {str(row.id): row for row in rows}
    def source(row, quote):
        return {"document": name, "page": row.page, "section": row.section, "quote": quote}

    sources = [
        source(references[citation["source_id"]], citation["quote"])
        for citation in citations
        if citation["source_id"] in references and citation["version"] == 1 and citation["quote"]
        and citation["quote"] in references[citation["source_id"]].content
    ]
    if not sources or len(sources) != len(citations):
        return {"answer": None, "sources": [
            source(row, row.content) for row in rows
        ]}
    return {"answer": output["text"], "sources": sources}
