"""Lectura local de ID3. Nunca identifica grabaciones ni consulta internet."""

from dataclasses import dataclass, field
from io import BytesIO
import unicodedata

from mutagen.mp3 import MP3
from PIL import Image, UnidentifiedImageError


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
    tags = MP3(path).tags
    result = Tags()
    if not tags:
        return result

    def values(frame):
        text_frame = tags.get(frame)
        raw = getattr(text_frame, "text", [])
        output = []
        seen = set()
        for item in raw[:20]:
            value = clean_text(item)
            key = normalized(value)
            if value and len(key) <= 320 and key not in seen:
                output.append(value)
                seen.add(key)
        return output

    result.title = next(iter(values("TIT2")), None)
    result.artists = values("TPE1")
    result.album_title = next(iter(values("TALB")), None)
    result.album_artists = values("TPE2") or result.artists
    number = next(iter(values("TRCK")), "").split("/", 1)[0]
    if number.isdecimal() and 0 < int(number) <= 2_147_483_647:
        result.track_number = int(number)
    pictures = tags.getall("APIC")
    pictures.sort(key=lambda picture: int(picture.type) != 3)
    for picture in pictures[:5]:
        try:
            result.cover = prepare_cover(picture.data)
            break
        except ValueError:
            if "cover_ignored" not in result.warnings:
                result.warnings.append("cover_ignored")
    return result
