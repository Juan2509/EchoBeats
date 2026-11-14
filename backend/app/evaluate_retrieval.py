"""Puntúa resultados guardados de P17 sin red, modelos ni llamadas facturables."""
import argparse
import json
from math import log2
from pathlib import Path


def evaluate(cases, report, partition):
    if report.get('collection')!=cases['collection'] or report.get('k')!=3:
        raise ValueError('Colección o K incompatible con el protocolo P17 v1.')
    expected={q['id']:q for q in cases['queries'] if q['split']==partition}
    runs=report.get('runs',[])
    if len({r['query_id'] for r in runs})!=len(runs) or {r['query_id'] for r in runs}!=set(expected):
        raise ValueError('Se necesita exactamente un resultado por consulta de la partición, incluidos errores y negativos.')
    scores=[];negatives=[];errors=0
    for run in runs:
        q=expected[run['query_id']];ids=run.get('results',[])
        if not isinstance(ids,list) or len(ids)>3 or len(set(ids))!=len(ids) or not set(ids)<=set(cases['corpus']) or set(ids)&set(q.get('exclude',[])):
            raise ValueError('Resultados duplicados, desconocidos, referencia excluida o más de K.')
        decision=run.get('decision')
        if decision not in {'candidates','abstain','supported','error'}:raise ValueError('Decisión no válida.')
        if decision=='error':
            errors+=1;ids=[]
        if q['expected']=='results':
            grades=[q['grades'].get(identity,0) for identity in ids]
            ideal=sorted(q['grades'].values(),reverse=True)[:3]
            dcg=lambda values:sum((2**grade-1)/log2(position+2) for position,grade in enumerate(values))
            scores.append({'query_id':q['id'],'hit_at_3':int(2 in grades),'ndcg_at_3':dcg(grades)/dcg(ideal),
                'precision_returned':sum(g>=1 for g in grades)/len(grades) if grades else 0,
                'direct_coverage':grades.count(2)/list(q['grades'].values()).count(2)})
        elif q['expected']=='insufficient_evidence':
            negatives.append({'query_id':q['id'],'abstained':decision=='abstain','unsafe_supported':decision=='supported'})
    mean=lambda key:sum(row[key] for row in scores)/len(scores) if scores else 0
    abstentions=sum(row['abstained'] for row in negatives)
    return {'collection':cases['collection'],'partition':partition,'k':3,'positive_queries':len(scores),
        'hit_at_3':mean('hit_at_3'),'ndcg_at_3':mean('ndcg_at_3'),'precision_returned':mean('precision_returned'),
        'direct_coverage':mean('direct_coverage'),'negative_queries':len(negatives),
        'negative_abstentions':abstentions,'negative_unsafe_supported':sum(row['unsafe_supported'] for row in negatives),
        'errors':errors,'per_query':scores+negatives,
        'numerical_gates_met':bool(scores) and mean('hit_at_3')>=.8 and mean('ndcg_at_3')>=.8 and abstentions==len(negatives) and errors==0,
        'real_api_verified':False,'notice':'Solo puntúa el archivo recibido. No certifica origen de vectores, API real, citas ni calidad de explicaciones.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--cases',type=Path,default=Path('/app/semantic-fixtures/consultas.json'))
    parser.add_argument('--partition',choices=['desarrollo','reservada'],default='desarrollo')
    args=parser.parse_args()
    try:
        value=evaluate(json.loads(args.cases.read_text(encoding='utf-8')),json.loads(args.report.read_text(encoding='utf-8')),args.partition)
    except (ValueError,KeyError,TypeError,OSError) as exc:
        parser.exit(2,f'No se pudo evaluar el informe: {exc}\n')
    print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
