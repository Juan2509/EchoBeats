"""Fixtures originales reproducibles. Requiere FFmpeg solo para generarlas."""

import base64
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import struct
import subprocess
import wave

from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, TALB, TIT2, TPE1, TPE2, TRCK
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'pruebas' / 'coleccion' / 'multiformato'


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    source = DEST / 'tono.wav'
    with wave.open(str(source), 'wb') as output:
        output.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
        frames = bytearray()
        for index in range(110250):
            sample = round(6000 * math.sin(2 * math.pi * 440 * index / 44100))
            frames.extend(struct.pack('<hh', sample, sample))
        output.writeframes(frames)
    for name, codec in [('tono.flac', ['-c:a', 'flac']), ('tono.ogg', ['-c:a', 'libvorbis', '-q:a', '4']),
                        ('tono.opus', ['-c:a', 'libopus', '-b:a', '96k'])]:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), *codec, str(DEST / name)], check=True)
    image = BytesIO()
    Image.new('RGB', (32, 32), '#aac577').save(image, format='PNG')
    cover = image.getvalue()
    picture = Picture(); picture.type = 3; picture.mime = 'image/png'
    picture.width = picture.height = 32; picture.depth = 24; picture.data = cover
    records = []
    for number, (name, label, reader, mime) in enumerate([
        ('tono.wav', 'WAV', WAVE, 'audio/wav'), ('tono.flac', 'FLAC', FLAC, 'audio/flac'),
        ('tono.ogg', 'Vorbis', OggVorbis, 'audio/ogg'), ('tono.opus', 'Opus', OggOpus, 'audio/ogg'),
    ], start=1):
        path = DEST / name
        audio = reader(path)
        if isinstance(audio, WAVE):
            audio.add_tags()
            for frame in [TIT2(encoding=3, text=[f'Prueba {label}']), TALB(encoding=3, text=['Colección multiformato']),
                          TPE1(encoding=3, text=['Señal técnica EchoBeats']), TPE2(encoding=3, text=['Señal técnica EchoBeats']),
                          TRCK(encoding=3, text=[f'{number}/4']), APIC(encoding=3, mime='image/png', type=3, data=cover)]:
                audio.tags.add(frame)
        else:
            for key, value in {'title': f'Prueba {label}', 'album': 'Colección multiformato',
                               'artist': 'Señal técnica EchoBeats', 'albumartist': 'Señal técnica EchoBeats',
                               'tracknumber': f'{number}/4'}.items():
                audio[key] = [value]
            if isinstance(audio, FLAC):
                audio.add_picture(picture)
            else:
                audio['metadata_block_picture'] = [base64.b64encode(picture.write()).decode('ascii')]
        audio.save()
        payload = path.read_bytes()
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'], check=True)
        records.append({'file': name, 'title': f'Prueba {label}', 'mime_type': mime,
                        'duration_seconds': reader(path).info.length, 'bytes': len(payload),
                        'sha256': hashlib.sha256(payload).hexdigest()})
    manifest = {'origin': 'Señal sinusoidal original 440 Hz, estéreo, 2.5 s; sin música de terceros.',
                'generator': 'scripts/generar_audio_multiformato.py',
                'ffmpeg': subprocess.check_output(['ffmpeg', '-version'], text=True).splitlines()[0], 'files': records}
    (DEST / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
