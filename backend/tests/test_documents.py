import asyncio
from io import BytesIO
import shutil

from PIL import Image, ImageDraw, ImageFont
from pydantic import SecretStr
import pytest
from sqlalchemy import func, select

from app.integrations import pdf
from app.integrations.ai import OpenAIProvider
from app.models.documents import chunk, upload
from app.services import documents
from test_metadata import client


def scanned_pdf():
    image = Image.new("RGB", (1400, 800), "white")
    ImageDraw.Draw(image).text(
        (100, 160), "MUSICA DE PRUEBA\nARCHIVO MUSICAL", fill="black", font=ImageFont.load_default(72),
    )
    data = BytesIO()
    blank = Image.new("RGB", image.size, "white")
    blank.save(data, format="PDF", save_all=True, append_images=[image])
    return data.getvalue()


class Provider:
    def __init__(self, settings):
        self.model_key = OpenAIProvider(settings).model_key
        self.invalid = False

    async def embed(self, content):
        return {"model_key": self.model_key, "vector": [1.0] + [0.0] * 1535}

    async def generate(self, question, evidence):
        source = evidence[0]
        return {"output": {"text": "La fuente contiene música de prueba.", "evidence": [{
            "source_id": source["source_id"], "version": 1,
            "quote": "cita que no existe" if self.invalid else source["text"][:40],
        }]}}


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.skipif(
    any(not shutil.which(name) for name in ("clamscan", "pdfinfo", "tesseract")),
    reason="Requiere ClamAV, Poppler y Tesseract",
)
async def test_upload_ocr_queue_citations_and_retention(client, catalog_engine, monkeypatch, tmp_path):
    api, app = client
    app.state.settings = app.state.settings.model_copy(update={
        "documents_enabled": True, "ai_enabled": True, "processing_worker_enabled": True,
        "openai_api_key": SecretStr("fixture"),
    })
    provider = Provider(app.state.settings)
    app.state.ai_provider = provider
    signatures = tmp_path / "signatures"
    signatures.mkdir()
    monkeypatch.setattr(pdf, "SIGNATURES", signatures)
    assert not (await api.get("/api/v1/documents")).json()["upload_enabled"]
    (signatures / "fixture.ndb").write_text(
        "EchoBeats.Test.Only:0:*:4543484f42454154535f4e4f545f50524553454e54\n",
    )
    monkeypatch.setattr(pdf, "scanner_ready", lambda: True)
    route = "/api/v1/documents"
    headers = {"Content-Type": "application/pdf", "X-Document-Name": "prueba.pdf"}
    wrong = await api.post(route, headers=headers, content=b"invalid")
    assert wrong.status_code == 422
    response = await api.post(route, headers=headers, content=scanned_pdf())
    assert response.status_code == 202, response.text
    identity = response.json()["id"]

    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(upload)) == 1
    worker = documents.DocumentWorker(catalog_engine, app.state.settings, lambda settings: provider)
    assert documents.claim(catalog_engine) is not None
    worker.start()
    try:
        for _ in range(100):
            index = (await api.get(route)).json()["items"][0]
            if index["status"] in {"ready", "failed"}:
                break
            await asyncio.sleep(.1)
        assert index["status"] == "ready", index
    finally:
        worker.stop()
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(upload)) == 0
        assert connection.scalar(select(chunk.c.extraction)) == "ocr"

    query = route + "/" + identity + "/query"
    response = await api.post(query, json={"question": "¿Qué música contiene?"})
    assert response.status_code == 200, response.text
    assert response.json()["sources"][0]["page"] == 2
    assert "MUSICA DE PRUEBA" in response.json()["sources"][0]["quote"]
    assert response.json()["answer"]
    provider.invalid = True
    fallback = await api.post(query, json={"question": "¿Qué música contiene?"})
    assert fallback.json()["answer"] is None and fallback.json()["sources"]
    assert (await api.delete(route + "/" + identity)).status_code == 204
    assert (await api.post(query, json={"question": "¿Qué música contiene?"})).status_code == 404
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(chunk)) == 0


def test_page_splitting_stays_bounded_and_retains_overlap():
    text = " ".join(f"palabra{i}" for i in range(500))
    sections = list(pdf.split_page(text))
    assert len(sections) > 1
    assert all(0 < len(part) <= 1600 for part in sections)
    assert sections[0][-100:] in sections[1]
