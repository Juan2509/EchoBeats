"""Preferencias explícitas y acotadas; no aprende, no altera distancias ni RRF."""
from sqlalchemy import select
from app.models.catalog import favorite

POLICY = 'adjacent_pairs_v1'


def summary(mode, baseline=(), results=()):
    before = [str(item['track']['id']) for item in baseline]
    after = [str(item['track']['id']) for item in results]
    return {'mode': mode, 'policy': POLICY, 'baseline_order': before,
            'result_order': after, 'reordered': before != after}


def apply(connection, results, mode):
    # Recuperar siempre el orden de consulta, incluso al revalidar después de red.
    indexed = sorted(enumerate(results, 1), key=lambda pair: pair[1].get('preference', {}).get('base_rank', pair[0]))
    baseline = [item for _, item in indexed]
    ids = [item['track']['id'] for item in baseline]
    saved = {str(value) for value in connection.scalars(select(favorite.c.track_id).where(favorite.c.track_id.in_(ids)))}
    if mode == 'discovery':
        baseline = [item for item in baseline if str(item['track']['id']) not in saved]
    baseline = [{**item, 'preference': {'favorite': str(item['track']['id']) in saved, 'base_rank': rank}}
                for rank, item in enumerate(baseline, 1)]
    ordered = list(baseline)
    if mode == 'favorites':
        # Pares disjuntos (1,2), (3,4), ...: cada pista se desplaza como máximo uno.
        for index in range(0, len(ordered) - 1, 2):
            if not ordered[index]['preference']['favorite'] and ordered[index + 1]['preference']['favorite']:
                ordered[index], ordered[index + 1] = ordered[index + 1], ordered[index]
    annotated = []
    for rank, item in enumerate(ordered, 1):
        original = item['preference']['base_rank']
        reason = ('Favorito explícito: sube una posición dentro de su par de candidatos.' if rank < original else
                  'Cede una posición al favorito explícito de su mismo par.' if rank > original else
                  'Se excluyen favoritos guardados; se conserva el orden de consulta.' if mode == 'discovery' else
                  'Se conserva el orden de consulta; preferencias desactivadas.' if mode == 'off' else
                  'Sin cambio por favoritos dentro de su par de candidatos.')
        annotated.append({**item, 'preference': {**item['preference'], 'rank': rank, 'reason': reason}})
    return annotated, summary(mode, baseline, annotated)
