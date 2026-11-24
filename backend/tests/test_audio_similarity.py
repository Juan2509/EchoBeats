from io import BytesIO
import math
import os
import shutil
import struct
import subprocess
import sys
from uuid import UUID
import wave

import pytest

from app.integrations.audio_embedding import RATE, AudioEmbeddingError, embedding_from_pcm
from app.integrations.storage import MediaStore
from app.services.audio_similarity import acoustic_criterion, acoustic_profiles, describe_profile, index_audio, pending_tracks, recommend_by_profile
from test_metadata import client, upload


def tone(frequency, duration=1):
    return b"".join(
        struct.pack("<h", round(12000 * math.sin(math.tau * frequency * i / RATE)))
        for i in range(int(RATE * duration))
    )


def wav(pcm):
    output = BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setparams((1, 2, RATE, 0, "NONE", "not compressed"))
        writer.writeframes(pcm)
    return output.getvalue()


def test_audio_vectors_reflect_frequency_and_reject_silence():
    low = embedding_from_pcm(tone(440))
    nearby = embedding_from_pcm(tone(450))
    high = embedding_from_pcm(tone(2800))
    assert len(low) == 26
    assert sum(value**2 for value in low) == pytest.approx(1)
    assert sum(a*b for a, b in zip(low, nearby)) > sum(a*b for a, b in zip(low, high))
    with pytest.raises(AudioEmbeddingError):
        embedding_from_pcm(bytes(RATE * 2))


def test_profile_describes_measured_band_weight_and_spectral_variation():
    low = describe_profile(embedding_from_pcm(tone(150)))
    high = describe_profile(embedding_from_pcm(tone(2800)))
    changing = describe_profile(embedding_from_pcm(tone(150) + tone(2800)))
    assert low["frequency_weights"]["bass"] > high["frequency_weights"]["bass"]
    assert high["frequency_weights"]["treble"] > low["frequency_weights"]["treble"]
    assert changing["spectral_variation"] > low["spectral_variation"]
    assert "frecuencias graves" in low["summary"]
    assert describe_profile([0] * 26) is None
    assert acoustic_criterion("Dame canciones con frecuencias agudas") == "treble"
    assert acoustic_criterion("Busco un perfil espectral uniforme") == "stable"
    assert acoustic_criterion("Busco pistas sin graves marcados") is None
    assert acoustic_criterion("¿Cómo suena esta canción?") is None


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="Requiere FFmpeg")
async def test_real_audio_index_cosine_order_and_retired_track(client, catalog_engine):
    api, app = client
    ids = []
    originals = []
    for frequency in (440, 450, 2800):
        original = wav(tone(frequency))
        originals.append(original)
        ids.append((await upload(api, original, "mismo-titulo.wav"))["track_id"])

    route = f"/api/v1/tracks/{ids[0]}/audio-similar"
    assert (await api.get(route)).status_code == 409
    store = MediaStore(app.state.settings.media_root)
    with catalog_engine.connect() as connection:
        candidates = pending_tracks(connection)
    run = subprocess.run(
        [sys.executable, "-m", "app.index_audio"],
        env={**os.environ, "DATABASE_URL": catalog_engine.url.render_as_string(hide_password=False)},
        check=True, capture_output=True, text=True, timeout=30,
    )
    assert "Vectores nuevos: 3. Pistas con error: 0." in run.stdout
    assert not index_audio(catalog_engine, store, candidates[0])
    with catalog_engine.connect() as connection:
        assert pending_tracks(connection) == []
        profiles = acoustic_profiles(connection, [UUID(ids[2])])
    assert "frecuencias agudas" in profiles[UUID(ids[2])]["summary"]
    ranked = recommend_by_profile(catalog_engine, "treble", limit=1)
    assert str(ranked[0]["track"]["id"]) == ids[2]
    assert (await api.put(f"/api/v1/tracks/{ids[2]}/favorite", json={"favorite": True})).status_code == 200
    discovery = recommend_by_profile(catalog_engine, "treble", limit=1, discovery=True)
    assert str(discovery[0]["track"]["id"]) != ids[2]

    response = await api.get(route)
    assert response.status_code == 200, response.text
    results = response.json()["results"]
    assert [item["track"]["id"] for item in results] == ids[1:]
    assert results[0]["distance"] < results[1]["distance"]
    assert (await api.get(results[0]["track"]["audio_url"])).content == originals[1]

    track_route = f"/api/v1/tracks/{ids[1]}"
    version = (await api.get(track_route)).headers["etag"]
    assert (await api.delete(track_route, headers={"If-Match": version})).status_code == 200
    assert [item["track"]["id"] for item in (await api.get(route)).json()["results"]] == ids[2:]


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="Requiere FFmpeg")
async def test_worker_indexes_existing_and_new_audio_recovers_and_retries(client, catalog_engine, monkeypatch):
    import asyncio

    from app.models.catalog import audio_index_attempt
    from app.processing_worker import ProcessingWorker
    from app.services import audio_similarity

    api, app = client
    first = (await upload(api, wav(tone(440)), "primera.wav"))["track_id"]
    first_path = f"/api/v1/tracks/{first}"
    assert (await api.get(first_path + "/audio-index")).json() == {
        "status": "pending", "worker_enabled": False, "error": None,
    }
    assert (await api.post(first_path + "/audio-index/retry")).status_code == 409
    with catalog_engine.begin() as connection:
        candidate, = pending_tracks(connection)
        connection.execute(audio_index_attempt.insert().values(
            **audio_similarity.attempt_key(candidate), status="processing",
        ))

    app.state.settings = app.state.settings.model_copy(update={"processing_worker_enabled": True})
    embed = audio_similarity.embed_file
    failure_count = 0

    def fail_once(path):
        nonlocal failure_count
        if path.name != candidate.storage_key.split("/")[-1] and failure_count == 0:
            failure_count += 1
            raise AudioEmbeddingError("Fallo transitorio de prueba.")
        return embed(path)

    monkeypatch.setattr(audio_similarity, "embed_file", fail_once)

    async def wait_for(path, expected):
        for _ in range(100):
            state = (await api.get(path + "/audio-index")).json()
            if state["status"] == expected:
                return state
            await asyncio.sleep(.05)
        pytest.fail(f"No se alcanzó el estado {expected}: {state}")

    worker = ProcessingWorker(catalog_engine, interval=.02, settings=app.state.settings)
    worker.start()
    try:
        await wait_for(first_path, "ready")
        second = (await upload(api, wav(tone(450)), "segunda.wav"))["track_id"]
        second_path = f"/api/v1/tracks/{second}"
        assert (await wait_for(second_path, "failed"))["error"] == "Fallo transitorio de prueba."
    finally:
        worker.stop()

    worker = ProcessingWorker(catalog_engine, interval=.02, settings=app.state.settings)
    worker.start()
    try:
        await wait_for(second_path, "failed")
        response = await api.post(second_path + "/audio-index/retry")
        assert response.status_code == 200
        await wait_for(second_path, "ready")
        result = await api.get(first_path + "/audio-similar")
        assert [item["track"]["id"] for item in result.json()["results"]] == [second]
    finally:
        worker.stop()
