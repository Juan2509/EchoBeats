from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError

from app.config import Settings
from app.integrations.storage import MediaStore
from app.main import create_app
from app.media_audit import audit
from app.models.catalog import UNKNOWN_ALBUM_ID, album, media_asset, playlist, playlist_track, track
from app.services.imports import import_file

FIXTURES = Path("/app/fixtures")
if not FIXTURES.is_dir():
    FIXTURES = Path(__file__).resolve().parents[2] / "pruebas" / "coleccion"
pytestmark = pytest.mark.integration


def data(name="tono_grave.mp3"):
    return (FIXTURES / name).read_bytes()


def counts(engine):
    with engine.connect() as connection:
        return tuple(connection.scalar(select(func.count()).select_from(table)) for table in (track, media_asset))


@pytest.fixture
def app(catalog_engine, tmp_path):
    settings = Settings(_env_file=None, media_root=tmp_path / "media")
    application = create_app(settings)
    original = application.state.database_engine
    application.state.database_engine = catalog_engine
    yield application
    if original is not None:
        original.dispose()


@pytest.mark.anyio
async def test_mixed_batch_and_original_bytes(app, catalog_engine):
    names = ["tono_grave.mp3", "sin_etiquetas.mp3", "tono_grave_duplicado.mp3", "invalido.mp3", "vacio.mp3"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        response = await client.post("/api/v1/imports", files=[("files", (name, data(name), "audio/mpeg")) for name in names])
    assert response.status_code == 200
    results = response.json()["results"]
    assert [item["status"] for item in results] == ["imported", "imported", "duplicate", "rejected", "rejected"]
    assert results[0]["track_id"] == results[2]["track_id"]
    assert counts(catalog_engine) == (2, 2)
    store = MediaStore(app.state.settings.media_root)
    with catalog_engine.connect() as connection:
        for row in connection.execute(select(media_asset)):
            payload = store.path_for(row.storage_key).read_bytes()
            assert hashlib.sha256(payload).hexdigest() == row.sha256
        row = connection.execute(select(track).where(track.c.id == UUID(results[1]["track_id"]))).one()
        assert row.album_id == UNKNOWN_ALBUM_ID
        assert row.title == "sin_etiquetas"
        assert row.duration_ms > 11000
        assert row.metadata_sources["title"] == "fallback"
    assert not list((store.root / ".staging").iterdir())
    assert audit(catalog_engine, store)["missing_asset_ids"] == []


@pytest.mark.anyio
async def test_limits_and_wrong_form_do_not_persist(app, catalog_engine):
    settings = app.state.settings
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        settings.import_max_request_bytes = 500
        response = await client.post("/api/v1/imports", files={"files": ("large.mp3", data())})
        assert response.status_code == 413
        # Sin Content-Length: también se cuenta el stream real.
        boundary = "testboundary"
        async def chunks():
            yield (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"large.mp3\"\r\n\r\n").encode()
            yield data()
            yield f"\r\n--{boundary}--\r\n".encode()
        response = await client.post("/api/v1/imports", content=chunks(), headers={"content-type": f"multipart/form-data; boundary={boundary}"})
        assert response.status_code == 413
        settings.import_max_request_bytes = 200 * 1024 * 1024
        settings.import_max_file_bytes = 100
        response = await client.post("/api/v1/imports", files={"files": ("large.mp3", data())})
        assert response.json()["results"][0]["error"]["code"] == "file_too_large"
        settings.import_max_files = 1
        response = await client.post("/api/v1/imports", files=[("files", ("one.mp3", data())), ("files", ("two.mp3", data()))])
        assert response.status_code == 422
        assert (await client.post("/api/v1/imports", files={"wrong": ("a.mp3", data())})).status_code == 422
        assert (await client.post("/api/v1/imports", json={})).status_code == 415
    assert counts(catalog_engine) == (0, 0)


def test_parallel_duplicate_keeps_one_file_and_track(catalog_engine, tmp_path):
    store = MediaStore(tmp_path)
    def run(_):
        return import_file(catalog_engine, store, BytesIO(data()), "a.mp3", 1024 * 1024)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run, range(2)))
    assert sorted(item["status"] for item in results) == ["duplicate", "imported"]
    assert results[0]["track_id"] == results[1]["track_id"]
    assert counts(catalog_engine) == (1, 1)
    assert len(list((tmp_path / "audio").glob("*.mp3"))) == 1


def test_storage_failure_rolls_back_database(catalog_engine, tmp_path, monkeypatch):
    store = MediaStore(tmp_path)
    def fail(*_):
        raise OSError("Fallo de escritura inducido")
    monkeypatch.setattr(store, "publish", fail)
    result = import_file(catalog_engine, store, BytesIO(data()), "a.mp3", 1024 * 1024)
    assert result["error"]["code"] == "storage_unavailable"
    assert counts(catalog_engine) == (0, 0)


def test_database_failure_removes_only_new_uncommitted_file(catalog_engine, tmp_path):
    store = MediaStore(tmp_path)
    def fail_track(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO track "):
            raise IntegrityError(statement, {}, Exception("Fallo inducido"))
    event.listen(catalog_engine, "before_cursor_execute", fail_track)
    try:
        result = import_file(catalog_engine, store, BytesIO(data()), "a.mp3", 1024 * 1024)
    finally:
        event.remove(catalog_engine, "before_cursor_execute", fail_track)
    assert result["status"] == "rejected"
    assert counts(catalog_engine) == (0, 0)
    assert list((tmp_path / "audio").glob("*.mp3")) == []


def test_ambiguous_commit_preserves_confirmed_media(catalog_engine, tmp_path):
    class LostCommitResponse:
        @contextmanager
        def begin(self):
            with catalog_engine.begin() as connection:
                yield connection
            raise OperationalError("COMMIT", {}, Exception("Respuesta perdida"))
        def connect(self):
            return catalog_engine.connect()
    store = MediaStore(tmp_path)
    result = import_file(LostCommitResponse(), store, BytesIO(data()), "a.mp3", 1024 * 1024)
    assert result["status"] == "imported"
    assert counts(catalog_engine) == (1, 1)
    assert audit(catalog_engine, store)["missing_asset_ids"] == []


def test_catalog_constraints_and_playlist_order(catalog_engine, tmp_path):
    store = MediaStore(tmp_path)
    ids = [UUID(import_file(catalog_engine, store, BytesIO(data(name)), name, 1024 * 1024)["track_id"]) for name in ("tono_grave.mp3", "tono_agudo.mp3")]
    with catalog_engine.begin() as connection:
        list_id = connection.scalar(playlist.insert().values(name="Prueba").returning(playlist.c.id))
        connection.execute(playlist_track.insert().values(playlist_id=list_id, track_id=ids[0], position=0))
    with pytest.raises(IntegrityError):
        with catalog_engine.begin() as connection:
            connection.execute(playlist_track.insert().values(playlist_id=list_id, track_id=ids[1], position=0))
    with pytest.raises(IntegrityError):
        with catalog_engine.begin() as connection:
            connection.execute(album.delete().where(album.c.id == UNKNOWN_ALBUM_ID))
    with pytest.raises(IntegrityError):
        with catalog_engine.begin() as connection:
            connection.execute(media_asset.delete())
    with pytest.raises(IntegrityError):
        with catalog_engine.begin() as connection:
            connection.execute(track.insert().values(audio_asset_id=uuid4(), content_sha256="b" * 64, album_id=UNKNOWN_ALBUM_ID, title="Huérfana", duration_ms=1000))
    assert counts(catalog_engine) == (2, 2)


def test_lost_original_can_be_restored_by_duplicate(catalog_engine, tmp_path):
    store = MediaStore(tmp_path)
    first = import_file(catalog_engine, store, BytesIO(data()), "a.mp3", 1024 * 1024)
    with catalog_engine.connect() as connection:
        key = connection.scalar(select(media_asset.c.storage_key))
    store.path_for(key).unlink()
    result = import_file(catalog_engine, store, BytesIO(data()), "b.mp3", 1024 * 1024)
    assert result["status"] == "duplicate" and result["track_id"] == first["track_id"]
    assert store.path_for(key).read_bytes() == data()
