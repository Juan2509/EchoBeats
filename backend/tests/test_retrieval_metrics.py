import pytest
from app.evaluate_retrieval import evaluate

CASES={'collection':'control','corpus':['A','B','C'],'queries':[
    {'id':'Q1','split':'desarrollo','expected':'results','grades':{'A':2,'B':1},'exclude':['C']},
    {'id':'Q2','split':'desarrollo','expected':'insufficient_evidence','grades':{}}]}


def report(results=None,decision='candidates'):
    return {'collection':'control','k':3,'runs':[{'query_id':'Q1','results':results if results is not None else ['A','B'],'decision':decision},{'query_id':'Q2','results':[],'decision':'abstain'}]}


def test_metrics_ideal_is_one_without_claiming_real_api():
    value=evaluate(CASES,report(),'desarrollo')
    assert value['hit_at_3']==1 and value['ndcg_at_3']==1 and value['precision_returned']==1
    assert value['numerical_gates_met'] is True and value['real_api_verified'] is False


def test_errors_and_empty_positive_are_not_removed_from_denominator():
    value=evaluate(CASES,report([],decision='error'),'desarrollo')
    assert value['positive_queries']==1 and value['hit_at_3']==0 and value['ndcg_at_3']==0
    assert value['errors']==1 and value['numerical_gates_met'] is False


def test_partial_ranking_scores_lower_and_candidates_are_not_abstention():
    value=report(['B','A']);value['runs'][1]['decision']='candidates'
    metrics=evaluate(CASES,value,'desarrollo')
    assert 0<metrics['ndcg_at_3']<1 and metrics['negative_abstentions']==0 and not metrics['numerical_gates_met']


def test_cannot_hide_queries_or_include_excluded_reference():
    value=report();value['runs'].pop()
    with pytest.raises(ValueError):evaluate(CASES,value,'desarrollo')
    with pytest.raises(ValueError):evaluate(CASES,report(['C']),'desarrollo')
    with pytest.raises(ValueError):evaluate(CASES,report(['A','A']),'desarrollo')
