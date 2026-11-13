"""Lectura local de ID3 y Vorbis Comments; sin reescribir originales."""

from dataclasses import dataclass, field
from io import BytesIO
import unicodedata
import base64
import binascii

from mutagen.mp3 import MP3
from mutagen import MutagenError
from mutagen.wave import WAVE
from mutagen.flac import Picture
from PIL import Image, UnidentifiedImageError
from app.integrations.audio_formats import load_audio


def clean_text(value: str) -> str:
    return " ".join(str(value).replace("\x00", "").split())[:255]


def normalized(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


@dataclass
class Cover:
    data: bytes
    width: int
    height: int


def prepare_cover(data: bytes) -> Cover:
    if not data or len(data) > 5 * 1024 * 1024:
        raise ValueError("La portada supera el límite de 5 MiB o está vacía.")
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in {"PNG", "JPEG"}:
                raise ValueError("La portada debe ser PNG o JPEG.")
            if max(image.size) > 4096 or image.width * image.height > 16_000_000:
                raise ValueError("La portada supera las dimensiones permitidas.")
            image.verify()
        with Image.open(BytesIO(data)) as image:
            image.load()
            image.thumbnail((1024, 1024))
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            output = BytesIO()
            # Re-encode sin metadatos, scripts ni contenido extra del original.
            clean = Image.new(image.mode, image.size)
            clean.paste(image)
            clean.save(output, format="PNG")
            return Cover(output.getvalue(), clean.width, clean.height)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("No se pudo validar la imagen de portada.") from exc


@dataclass
class Tags:
    title: str | None = None
    artists: list[str] = field(default_factory=list)
    album_title: str | None = None
    album_artists: list[str] = field(default_factory=list)
    track_number: int | None = None
    cover: Cover | None = None
    warnings: list[str] = field(default_factory=list)


def read_tags(path) -> Tags:
    audio = load_audio(path)
    tags = audio.tags
    result = Tags()
    if not tags and not getattr(audio, 'pictures', []):
        return result

    id3 = isinstance(audio, (MP3, WAVE))

    def values(frame):
        text_frame = tags.get(frame) if tags is not None else None
        raw = getattr(text_frame, "text", []) if id3 else (text_frame or [])
        output = []
        seen = set()
        for item in raw[:20]:
            value = clean_text(item)
            key = normalized(value)
            if value and len(key) <= 320 and key not in seen:
                output.append(value)
                seen.add(key)
        return output

    result.title = next(iter(values('TIT2' if id3 else 'title')), None)
    result.artists = values('TPE1' if id3 else 'artist')
    result.album_title = next(iter(values('TALB' if id3 else 'album')), None)
    result.album_artists = (values('TPE2') if id3 else values('albumartist') or values('album artist')) or result.artists
    number = next(iter(values('TRCK' if id3 else 'tracknumber')), '').split('/', 1)[0]
    if number.isdecimal() and 0 < int(number) <= 2_147_483_647:
        result.track_number = int(number)
    pictures = tags.getall('APIC') if id3 and tags else list(getattr(audio, 'pictures', []))
    if not id3 and tags:
        for encoded in tags.get('metadata_block_picture', [])[:5]:
            try:
                if len(encoded) > 7 * 1024 * 1024:
                    raise ValueError('Portada demasiado grande.')
                pictures.append(Picture(base64.b64decode(encoded, validate=True)))
            except (ValueError, binascii.Error, MutagenError):
                if 'cover_ignored' not in result.warnings:
                    result.warnings.append('cover_ignored')
    pictures.sort(key=lambda picture: int(picture.type) != 3)
    for picture in pictures[:5]:
        try:
            result.cover = prepare_cover(picture.data)
            break
        except ValueError:
            if "cover_ignored" not in result.warnings:
                result.warnings.append("cover_ignored")
    return result
