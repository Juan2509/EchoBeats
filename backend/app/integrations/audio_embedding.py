"""Deterministic embedding of decoded sound, with a versioned feature layout."""

import math
from pathlib import Path
import struct
import subprocess


MODEL_KEY = "pcm-mono-8k-spectrum-v1"
DIMENSIONS = 26
RATE = 8000
SECONDS = 30
FRAME = 256
BAND_EDGES = (1, 2, 3, 4, 6, 9, 13, 19, 27, 38, 54, 80, 129)
WINDOW = tuple(0.5 - 0.5 * math.cos(math.tau * i / (FRAME - 1)) for i in range(FRAME))
BIT_REVERSED = tuple(int(f"{i:08b}"[::-1], 2) for i in range(FRAME))
TWIDDLES = tuple(complex(math.cos(-math.tau*i/FRAME), math.sin(-math.tau*i/FRAME)) for i in range(FRAME // 2))


class AudioEmbeddingError(Exception):
    pass


def spectrum(samples):
    values = [samples[i] * WINDOW[i] for i in BIT_REVERSED]
    for width in (2, 4, 8, 16, 32, 64, 128, FRAME):
        half = width // 2
        for start in range(0, FRAME, width):
            for offset in range(half):
                even, odd = start + offset, start + offset + half
                product = TWIDDLES[offset * (FRAME // width)] * values[odd]
                values[even], values[odd] = values[even] + product, values[even] - product
    return [value.real**2 + value.imag**2 for value in values[:FRAME//2+1]]


def embedding_from_pcm(pcm: bytes) -> list[float]:
    samples = [sample / 32768 for sample, in struct.iter_unpack("<h", pcm)]
    observations = []
    for start in range(0, len(samples) - FRAME + 1, FRAME):
        frame = samples[start:start+FRAME]
        rms = math.sqrt(sum(sample**2 for sample in frame) / FRAME)
        if rms < 0.001:
            continue
        power = spectrum(frame)
        total = sum(power[1:])
        if total <= 1e-12:
            continue
        profile = [math.sqrt(sum(power[low:high]) / total) for low, high in zip(BAND_EDGES, BAND_EDGES[1:])]
        observations.append([*profile, rms])
    if not observations:
        raise AudioEmbeddingError("El audio no tiene suficiente señal en los primeros 30 segundos.")
    columns = list(zip(*observations))
    means = [sum(column) / len(column) for column in columns]
    deviations = [math.sqrt(sum((value-mean)**2 for value in column) / len(column)) for column, mean in zip(columns, means)]
    vector = means + deviations
    norm = math.sqrt(sum(value**2 for value in vector))
    return [value / norm for value in vector]


def embed_file(path: Path) -> list[float]:
    try:
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-protocol_whitelist", "file,pipe",
             "-threads", "1", "-i", str(path), "-map", "0:a:0", "-vn",
             "-t", str(SECONDS), "-ac", "1", "-ar", str(RATE), "-f", "s16le", "pipe:1"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=20, check=True,
        )
    except FileNotFoundError:
        raise AudioEmbeddingError("FFmpeg no está instalado en el servidor.") from None
    except (subprocess.SubprocessError, OSError):
        raise AudioEmbeddingError("No se pudo decodificar el audio dentro del límite de análisis.") from None
    if len(result.stdout) > RATE * SECONDS * 2 or len(result.stdout) % 2:
        raise AudioEmbeddingError("La salida PCM no tiene un tamaño válido.")
    return embedding_from_pcm(result.stdout)
