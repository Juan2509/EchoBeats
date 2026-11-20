"""Tipo pgvector fijo sin dependencia adicional; parámetros siempre enlazados."""
import json
import math
from sqlalchemy import cast
from sqlalchemy.types import UserDefinedType


class Vector(UserDefinedType):
    cache_ok = True

    dimensions: int

    def get_col_spec(self, **kw):
        return f'VECTOR({self.dimensions})'

    def bind_expression(self, value):
        return cast(value, self)

    def bind_processor(self, dialect):
        def process(value):
            if not isinstance(value, list) or len(value) != self.dimensions or not all(type(v) in (float, int) and math.isfinite(v) and abs(v) <= 3.402823e38 for v in value) or not any(v != 0 for v in value):
                raise ValueError(f'Vector no válido para el espacio de {self.dimensions} dimensiones.')
            return json.dumps(value, allow_nan=False, separators=(',', ':'))
        return process

    def result_processor(self, dialect, coltype):
        return lambda value: json.loads(value) if isinstance(value, str) else value


class Vector1536(Vector):
    dimensions = 1536
    cache_ok = True


class AudioVector26(Vector):
    dimensions = 26
    cache_ok = True
