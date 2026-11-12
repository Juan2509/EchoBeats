"""Genera señales MP3 técnicas originales; requiere Python y libmp3lame.

No descarga grabaciones, no llama APIs y no modifica archivos fuera de la colección.
Ejecutar desde la raíz: python3 scripts/generar_coleccion_prueba.py
"""

import ctypes
import ctypes.util
import hashlib
import json
import math
from pathlib import Path


DESTINO = Path(__file__).resolve().parents[1] / "pruebas" / "coleccion"
FRECUENCIA = 44100
SEGUNDOS = 12
PISTAS = [
    ("T01", "tono_grave.mp3", 220, False, "Álbum técnico A", "Tono grave"),
    ("T02", "pulsos_medios.mp3", 440, True, "Álbum técnico A", "Pulsos medios"),
    ("T03", "tono_agudo.mp3", 880, False, "Álbum técnico B", "Tono agudo"),
    ("T04", "sin_etiquetas.mp3", 330, True, None, None),
]


def configurar_biblioteca():
    nombre = ctypes.util.find_library("mp3lame")
    if not nombre:
        raise SystemExit("Se requiere libmp3lame para regenerar los MP3; no se instala automáticamente.")
    lib = ctypes.CDLL(nombre)
    lib.lame_init.restype = ctypes.c_void_p
    for funcion in ("lame_set_in_samplerate", "lame_set_num_channels", "lame_set_brate"):
        getattr(lib, funcion).argtypes = [ctypes.c_void_p, ctypes.c_int]
        getattr(lib, funcion).restype = ctypes.c_int
    for funcion in ("lame_init_params", "lame_close"):
        getattr(lib, funcion).argtypes = [ctypes.c_void_p]
        getattr(lib, funcion).restype = ctypes.c_int
    lib.id3tag_init.argtypes = [ctypes.c_void_p]
    for funcion in ("id3tag_set_title", "id3tag_set_artist", "id3tag_set_album"):
        getattr(lib, funcion).argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.lame_encode_buffer.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(ctypes.c_short), ctypes.POINTER(ctypes.c_short),
        ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int,
    ]
    lib.lame_encode_buffer.restype = ctypes.c_int
    lib.lame_encode_flush.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
    lib.lame_encode_flush.restype = ctypes.c_int
    return lib


def codificar(lib, frecuencia, pulsos, album, titulo):
    estado = lib.lame_init()
    if not estado:
        raise RuntimeError("No se pudo iniciar el codificador MP3")
    try:
        for funcion, valor in (
            (lib.lame_set_in_samplerate, FRECUENCIA),
            (lib.lame_set_num_channels, 1),
            (lib.lame_set_brate, 64),
        ):
            if funcion(estado, valor) < 0:
                raise RuntimeError("Configuración MP3 rechazada")
        if titulo:
            lib.id3tag_init(estado)
            # ID3v1 admite Latin-1. No se requiere una biblioteca de etiquetas adicional.
            lib.id3tag_set_title(estado, titulo.encode("latin-1"))
            lib.id3tag_set_album(estado, album.encode("latin-1"))
            lib.id3tag_set_artist(estado, b"EchoBeats - prueba sintetica")
        if lib.lame_init_params(estado) < 0:
            raise RuntimeError("No se pudieron iniciar los parámetros MP3")
        salida = bytearray()
        buffer = (ctypes.c_ubyte * 16384)()
        for inicio in range(0, FRECUENCIA * SEGUNDOS, 4096):
            cantidad = min(4096, FRECUENCIA * SEGUNDOS - inicio)
            muestras = (ctypes.c_short * cantidad)()
            for i in range(cantidad):
                t = (inicio + i) / FRECUENCIA
                borde = min(1, t / 0.05, (SEGUNDOS - t) / 0.05)
                envolvente = (0.25 + 0.75 * math.sin(math.pi * 2 * t) ** 2) if pulsos else 1
                muestras[i] = int(6500 * borde * envolvente * math.sin(2 * math.pi * frecuencia * t))
            usados = lib.lame_encode_buffer(estado, muestras, muestras, cantidad, buffer, len(buffer))
            if usados < 0:
                raise RuntimeError(f"Falló la codificación MP3: {usados}")
            salida.extend(bytes(buffer[:usados]))
        usados = lib.lame_encode_flush(estado, buffer, len(buffer))
        if usados < 0:
            raise RuntimeError(f"Falló el cierre MP3: {usados}")
        salida.extend(bytes(buffer[:usados]))
        return bytes(salida)
    finally:
        lib.lame_close(estado)


def main():
    lib = configurar_biblioteca()
    DESTINO.mkdir(parents=True, exist_ok=True)
    registros = []

    def registrar(identificador, archivo, contenido, **datos):
        (DESTINO / archivo).write_bytes(contenido)
        registros.append({
            "id": identificador, "archivo": archivo, "bytes": len(contenido),
            "sha256": hashlib.sha256(contenido).hexdigest(), **datos,
        })

    for identificador, archivo, frecuencia, pulsos, album, titulo in PISTAS:
        contenido = codificar(lib, frecuencia, pulsos, album, titulo)
        registrar(
            identificador, archivo, contenido, valido=True,
            duracion_senal_segundos=SEGUNDOS, frecuencia_muestreo_hz=FRECUENCIA,
            frecuencia_tono_hz=frecuencia, amplitud_pulsante=pulsos,
            titulo=titulo, album=album,
            artista="EchoBeats - prueba sintetica" if titulo else None,
            portada_incrustada=False,
            descripcion_verificada=f"Señal sinusoidal sintética de {frecuencia} Hz, mono, "
            + ("con amplitud pulsante." if pulsos else "con amplitud estable salvo entrada y salida."),
            fuente_descripcion="Parámetros del generador; sin análisis mediante IA.",
        )
    registrar("T05", "tono_grave_duplicado.mp3", (DESTINO / "tono_grave.mp3").read_bytes(),
              valido=True, duplicado_de="T01")
    registrar("T06", "invalido.mp3", b"EchoBeats: archivo de texto, no contiene audio.\n", valido=False)
    registrar("T07", "vacio.mp3", b"", valido=False)
    manifiesto = {
        "version": 1,
        "procedencia": "Señales originales generadas matemáticamente para EchoBeats; sin grabaciones de terceros.",
        "uso": "Pruebas, modificación y demostración dentro del proyecto EchoBeats.",
        "generador": "scripts/generar_coleccion_prueba.py",
        "codificador": "libmp3lame del sistema, 64 kbps mono; el resultado puede variar entre versiones.",
        "archivos": registros,
    }
    (DESTINO / "manifiesto.json").write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(f"Generados {len(registros)} archivos y manifiesto en {DESTINO}")


if __name__ == "__main__":
    main()
