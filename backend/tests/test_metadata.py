import hashlib
from io import BytesIO
from pathlib import Path
from uuid import UUID

from httpx import ASGITransport, AsyncClient
from mutagen.id3 import APIC, TALB, TIT2, TPE1, TPE2, TRCK
from mutagen.mp3 import MP3
from PIL import Image
import pytest
from sqlalchemy import func, select

from app.config import Settings
from app.main import create_app
from app.models.catalog import UNKNOWN_ALBUM_ID, album, media_asset, track
from app.integrations.storage import MediaStore
from app.media_audit import audit

pytestmark = [pytest.mark.integration, pytest.mark.anyio]
FIXTURES = Path("/app/fixtures")
if not FIXTURES.is_dir():
    FIXTURES = Path(__file__).resolve().parents[2] / "pruebas" / "coleccion"


def png(color="purple"):
    output = BytesIO()
    Image.new("RGB", (40, 30), color).save(output, format="PNG")
    return output.getvalue()


def tagged(title="Canción etiquetada", collection="Colección", names=None, picture=None):
    stream = BytesIO((FIXTURES / "sin_etiquetas.mp3").read_bytes())
    audio = MP3(stream)
    audio.add_tags()
    audio.tags.add(TIT2(encoding=3, text=[title]))
    audio.tags.add(TALB(encoding=3, text=[collection]))
    audio.tags.add(TPE1(encoding=3, text=names or ["Artista de prueba"]))
    audio.tags.add(TPE2(encoding=3, text=names or ["Artista de prueba"]))
    audio.tags.add(TRCK(encoding=3, text=["2/10"]))
    if picture is not None:
        audio.tags.add(APIC(encoding=3, mime="image/png", type=3, desc="Portada", data=picture))
    audio.save(stream, v1=0)
    return stream.getvalue()


@pytest.fixture
async def client(catalog_engine, tmp_path):
    app = create_app(Settings(_env_file=None, media_root=tmp_path))
    original = app.state.database_engine
    app.state.database_engine = catalog_engine
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as session:
        yield session, app
    if original is not None:
        original.dispose()


async def upload(client, payload, name="archivo.mp3"):
    result = await client.post("/api/v1/imports", files={"files": (name, payload, "audio/mpeg")})
    assert result.status_code == 200, result.text
    item = result.json()["results"][0]
    assert item["status"] in {"imported", "duplicate"}, item
    return item


async def test_id3v1_and_v2_cover_and_unchanged_original(client, catalog_engine):
    api, app = client
    original = tagged(names=["Artista uno", "Artista dos"], picture=png())
    item = await upload(api, original)
    assert not item.get("metadata_warnings"), item
    response = await api.get(f"/api/v1/tracks/{item['track_id']}")
    data = response.json()
    assert data["title"] == "Canción etiquetada"
    assert [value["name"] for value in data["artists"]] == ["Artista uno", "Artista dos"]
    assert data["album_title"] == "Colección" and data["track_number"] == 2
    assert data["metadata_sources"]["title"] == "file"
    assert data["duration_ms"] > 11000
    cover = await api.get(data["cover_url"])
    assert cover.status_code == 200 and cover.headers["content-type"] == "image/png"
    assert cover.headers["x-content-type-options"] == "nosniff"
    with Image.open(BytesIO(cover.content)) as image:
        assert image.size == (40, 30)
    with catalog_engine.connect() as connection:
        resource = connection.execute(select(media_asset).where(media_asset.c.kind == "audio")).one()
        assert MediaStore(app.state.settings.media_root).path_for(resource.storage_key).read_bytes() == original
        assert resource.sha256 == hashlib.sha256(original).hexdigest()
    legacy = await upload(api, (FIXTURES / "tono_grave.mp3").read_bytes())
    data = (await api.get(f"/api/v1/tracks/{legacy['track_id']}")).json()
    assert data["title"] == "Tono grave" and data["album_title"] == "Álbum técnico A"


async def test_no_tags_manual_edits_survive_reread_and_stale_patch(client):
    api, _ = client
    item = await upload(api, (FIXTURES / "sin_etiquetas.mp3").read_bytes(), "sin_etiquetas.mp3")
    url = f"/api/v1/tracks/{item['track_id']}"
    initial = await api.get(url)
    data = initial.json()
    assert data["title"] == "sin_etiquetas" and data["album_id"] == str(UNKNOWN_ALBUM_ID)
    assert data["artists"] == [] and data["cover_url"] is None
    assert (await api.patch(url, json={"title": "Corrección"})).status_code == 428
    new_album = await api.post("/api/v1/albums", json={"title": "Mi álbum", "artist_names": ["Mi artista"]})
    assert new_album.status_code == 201
    changed = await api.patch(url, headers={"If-Match": initial.headers["etag"]}, json={
        "title": "Corregida", "artist_names": ["Mi artista"], "album_id": new_album.json()["id"], "track_number": 7,
    })
    assert changed.status_code == 200, changed.text
    assert (await api.patch(url, headers={"If-Match": initial.headers["etag"]}, json={"title": "Vieja"})).status_code == 412
    extracted = await api.post(url + "/extract-metadata", headers={"If-Match": changed.headers["etag"]})
    assert extracted.status_code == 200, extracted.text
    assert extracted.json()["title"] == "Corregida" and extracted.json()["track_number"] == 7
    assert extracted.json()["album_title"] == "Mi álbum"
    assert extracted.json()["artists"][0]["name"] == "Mi artista"
    assert (await api.get(url)).json()["metadata_sources"]["title"] == "manual"


async def test_manual_corrections_override_real_tags_and_clear_values(client):
    api, _ = client
    item = await upload(api, tagged(picture=png()))
    url = f"/api/v1/tracks/{item['track_id']}"
    before = await api.get(url)
    update = await api.patch(url, headers={"If-Match": before.headers["etag"]}, json={
        "title": "Mi título", "artist_names": [], "track_number": None, "cover_asset_id": None,
    })
    assert update.status_code == 200, update.text
    reread = await api.post(url + "/extract-metadata", headers={"If-Match": update.headers["etag"]})
    data = reread.json()
    assert data["title"] == "Mi título" and data["artists"] == [] and data["track_number"] is None
    assert data["cover_url"] is None and data["cover_source"] == "manual"
    repeated = await upload(api, tagged(picture=png()))
    assert repeated["status"] == "duplicate"
    assert (await api.get(url)).json()["title"] == "Mi título"


async def test_album_grouping_credits_and_shared_manual_rename(client, catalog_engine):
    api, _ = client
    first = await upload(api, tagged(title="Primera", names=["Artista A"]))
    second = await upload(api, tagged(title="Segunda", names=["Artista A"]))
    other = await upload(api, tagged(title="Otra", names=["Artista B"]))
    details = [(await api.get(f"/api/v1/tracks/{item['track_id']}")).json() for item in (first, second, other)]
    assert details[0]["album_id"] == details[1]["album_id"] != details[2]["album_id"]
    album_url = f"/api/v1/albums/{details[0]['album_id']}"
    collection = await api.get(album_url)
    updated = await api.patch(album_url, headers={"If-Match": collection.headers["etag"]}, json={"title": "Nombre corregido"})
    assert updated.status_code == 200
    assert (await api.get(f"/api/v1/tracks/{second['track_id']}")).json()["album_title"] == "Nombre corregido"
    current = await api.get(f"/api/v1/tracks/{first['track_id']}")
    reread = await api.post(f"/api/v1/tracks/{first['track_id']}/extract-metadata", headers={"If-Match": current.headers["etag"]})
    assert reread.json()["album_title"] == "Nombre corregido"
    assert reread.json()["album_id"] == details[0]["album_id"]
    incoming = await upload(api, tagged(title="Nueva pista", names=["Artista A"]))
    incoming_data = (await api.get(f"/api/v1/tracks/{incoming['track_id']}")).json()
    assert incoming_data["album_id"] == details[0]["album_id"]
    assert incoming_data["album_title"] == "Nombre corregido"
    with catalog_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(album).where(album.c.system_key == "unknown")) == 1


async def test_bad_cover_does_not_reject_music_and_manual_cover_is_validated(client, catalog_engine):
    api, app = client
    item = await upload(api, tagged(picture=b"<svg>not a bitmap</svg>"))
    assert item["status"] == "imported" and item["metadata_warnings"] == ["cover_ignored"]
    url = f"/api/v1/tracks/{item['track_id']}"
    before = await api.get(url)
    assert before.json()["cover_url"] is None
    rejected = await api.post("/api/v1/assets", files={"file": ("wrong.png", b"text", "image/png")}, data={"purpose": "cover"})
    assert rejected.status_code == 422
    cover = await api.post("/api/v1/assets", files={"file": ("cover.png", png(), "application/octet-stream")}, data={"purpose": "cover"})
    assert cover.status_code == 201, cover.text
    patched = await api.patch(url, headers={"If-Match": before.headers["etag"]}, json={"cover_asset_id": cover.json()["id"]})
    assert patched.status_code == 200 and patched.json()["cover_source"] == "manual"
    assert (await api.get(patched.json()["cover_url"])).status_code == 200
    assert audit(catalog_engine, MediaStore(app.state.settings.media_root))["unreferenced_files"] == []


async def test_validation_no_audio_as_cover_and_system_album_protection(client, catalog_engine):
    api, _ = client
    item = await upload(api, tagged())
    url = f"/api/v1/tracks/{item['track_id']}"
    before = await api.get(url)
    for body in ({"title": " "}, {"title": None}, {"duration_ms": 1}, {"artist_names": ["A", "a"]}, {"track_number": 0}, {"track_number": True}):
        assert (await api.patch(url, headers={"If-Match": before.headers["etag"]}, json=body)).status_code == 422
    with catalog_engine.connect() as connection:
        audio_id = connection.scalar(select(track.c.audio_asset_id).where(track.c.id == UUID(item["track_id"])))
    assert (await api.patch(url, headers={"If-Match": before.headers["etag"]}, json={"cover_asset_id": str(audio_id)})).status_code == 422
    assert (await api.get(f"/api/v1/assets/{audio_id}/content")).status_code == 404
    unknown = await api.get(f"/api/v1/albums/{UNKNOWN_ALBUM_ID}")
    assert (await api.patch(f"/api/v1/albums/{UNKNOWN_ALBUM_ID}", headers={"If-Match": unknown.headers["etag"]}, json={"title": "Changed"})).status_code == 422
    assert (await api.get("/api/v1/tracks?limit=0")).status_code == 422
    assert (await api.get("/api/v1/tracks?limit=1&offset=0")).json()["total"] == 1


async def test_cover_not_shared_between_unidentified_albums(client):
    api, _ = client
    with_cover = await upload(api, tagged(names=["Artist"], collection="", picture=png()))
    without = await upload(api, (FIXTURES / "sin_etiquetas.mp3").read_bytes())
    first = (await api.get(f"/api/v1/tracks/{with_cover['track_id']}")).json()
    second = (await api.get(f"/api/v1/tracks/{without['track_id']}")).json()
    assert first["album_id"] == second["album_id"] == str(UNKNOWN_ALBUM_ID)
    assert first["cover_url"] and second["cover_url"] is None


async def test_album_manual_cover_keeps_group_and_is_not_overwritten(client):
    api, _ = client
    first = await upload(api, tagged(picture=png()))
    url = f"/api/v1/tracks/{first['track_id']}"
    before = await api.get(url)
    album_url = f"/api/v1/albums/{before.json()['album_id']}"
    collection = await api.get(album_url)
    new_cover = await api.post("/api/v1/assets", files={"file": ("blue.png", png("blue"), "image/png")}, data={"purpose": "cover"})
    updated = await api.patch(album_url, headers={"If-Match": collection.headers["etag"]}, json={"cover_asset_id": new_cover.json()["id"]})
    assert updated.status_code == 200
    reread = await api.post(url + "/extract-metadata", headers={"If-Match": before.headers["etag"]})
    assert reread.status_code == 200 and reread.json()["album_id"] == before.json()["album_id"]
    assert (await api.get(album_url)).json()["cover_asset_id"] == new_cover.json()["id"]
