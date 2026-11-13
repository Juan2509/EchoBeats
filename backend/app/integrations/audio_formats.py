"""Formatos admitidos por contenido; no confiar en el MIME del navegador."""

from dataclasses import dataclass
import math
from pathlib import Path
import wave

from mutagen import File
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE


AUDIO_MIME_TYPES = {'.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.flac': 'audio/flac',
                    '.ogg': 'audio/ogg', '.opus': 'audio/ogg'}
SUPPORTED_AUDIO = 'MP3, WAV PCM, FLAC, Ogg Vorbis y Ogg Opus'


@dataclass(frozen=True)
class AudioInfo:
    extension: str
    mime_type: str
    duration_ms: int


def load_audio(path):
    audio = File(path)
    if not isinstance(audio, (MP3, WAVE, FLAC, OggVorbis, OggOpus)):
        raise ValueError('El contenedor o códec de audio no está admitido.')
    return audio


def inspect_audio(path, extension: str) -> AudioInfo:
    audio = load_audio(path)
    if isinstance(audio, MP3):
        allowed, canonical = {'.mp3'}, '.mp3'
        if audio.info.layer != 3 or audio.info.sketchy:
            raise ValueError('Audio MPEG incompleto o distinto de MP3.')
    elif isinstance(audio, WAVE):
        allowed, canonical = {'.wav'}, '.wav'
        # WAV puede contener códecs comprimidos. La primera entrega admite PCM
        # entero y comprueba que el bloque data contenga las muestras declaradas.
        with wave.open(str(path), 'rb') as source:
            if source.getcomptype() != 'NONE' or source.getsampwidth() not in {1, 2, 3, 4}:
                raise ValueError('WAV requiere muestras PCM enteras de 8, 16, 24 o 32 bits.')
            expected = source.getnframes() * source.getsampwidth() * source.getnchannels()
            received = 0
            while chunk := source.readframes(65536):
                received += len(chunk)
            if received != expected:
                raise ValueError('El bloque de audio WAV está incompleto.')
    elif isinstance(audio, FLAC):
        allowed, canonical = {'.flac'}, '.flac'
    elif isinstance(audio, OggVorbis):
        allowed, canonical = {'.ogg'}, '.ogg'
    else:
        allowed, canonical = {'.ogg', '.opus'}, '.opus'
    if extension not in allowed:
        raise ValueError('La extensión no corresponde al contenido del archivo.')
    if not math.isfinite(audio.info.length) or audio.info.length <= 0 or audio.info.channels <= 0:
        raise ValueError('No se pudo determinar una duración y canales válidos.')
    duration_ms = max(1, round(audio.info.length * 1000))
    if duration_ms > 2_147_483_647:
        raise ValueError('La duración supera el límite del catálogo.')
    return AudioInfo(canonical, AUDIO_MIME_TYPES[canonical], duration_ms)


def stored_audio_type(key: str) -> str | None:
    return AUDIO_MIME_TYPES.get(Path(key).suffix.lower())
