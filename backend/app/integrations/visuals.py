"""Imágenes locales de muro verificadas; nunca se modifica el archivo del usuario."""
from dataclasses import dataclass
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from app.integrations.tags import Cover, prepare_cover

MAX_BYTES = 5 * 1024 * 1024
MAX_DECODED_PIXELS = 32_000_000


@dataclass
class Visual:
    data: bytes
    mime_type: str
    width: int
    height: int
    frames: int
    preview: Cover | None = None


def prepare_visual(data: bytes) -> Visual:
    if not data or len(data) > MAX_BYTES:
        raise ValueError('El recurso está vacío o supera 5 MiB.')
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in {'PNG', 'JPEG', 'GIF'}:
                raise ValueError('Utiliza una imagen PNG, JPEG o GIF.')
            width, height = image.size
            if max(width, height) > 4096 or width * height > 16_000_000:
                raise ValueError('La imagen supera 4096 píxeles por lado o 16 millones de píxeles.')
            kind = image.format
            frames = getattr(image, 'n_frames', 1)
            if kind != 'GIF' and frames != 1:
                raise ValueError('La animación debe estar en formato GIF; PNG animado no está admitido.')
            if frames > 200 or width * height * frames > MAX_DECODED_PIXELS:
                raise ValueError('El GIF supera 200 fotogramas o 32 millones de píxeles decodificados en total.')
            image.verify()
        with Image.open(BytesIO(data)) as image:
            if kind == 'GIF':
                first = None
                for index in range(frames):
                    image.seek(index)
                    if image.size != (width, height):
                        raise ValueError('El GIF cambia el tamaño del lienzo entre fotogramas.')
                    image.load()
                    if index == 0:
                        first = image.convert('RGBA')
                preview_stream = BytesIO()
                first.thumbnail((1024, 1024))
                first.save(preview_stream, format='PNG')
                preview = prepare_cover(preview_stream.getvalue())
                return Visual(data, 'image/gif', width, height, frames, preview)
            image.load()
            mode = 'RGBA' if image.mode in {'RGBA', 'LA', 'P'} else 'RGB'
            clean = Image.new(mode, image.size)
            clean.paste(image.convert(mode))
            stream = BytesIO()
            clean.save(stream, format='PNG')
            if len(stream.getvalue()) > MAX_BYTES:
                raise ValueError('La imagen normalizada supera 5 MiB. Reduce su tamaño antes de importarla.')
            return Visual(stream.getvalue(), 'image/png', width, height, 1)
    except (UnidentifiedImageError, OSError, EOFError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('No se pudo validar el archivo visual completo.') from None
