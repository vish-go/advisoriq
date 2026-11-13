from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from advisoriq import checker
from advisoriq.config import DATA
from advisoriq.guardrails import redact_pii, make_safe
from advisoriq.rag import research
from advisoriq.market import market_data, validate_symbol
from advisoriq.agent import run_advisor, message_text


@pytest.fixture(scope='session')
def model_path(tmp_path_factory):
    path = tmp_path_factory.mktemp('model') / 'checker.joblib'
    checker.train(path)
    return path


@pytest.fixture
def frame():
    return pd.DataFrame({'amount': [10, 50000], 'hour': [12, 2],
                         'is_foreign': [0, 1], 'merchant_risk': [0.05, 0.99]})


@pytest.mark.parametrize('column,value', [('amount', -1), ('amount', np.inf), ('hour', 24),
    ('hour', 1.5), ('is_foreign', 2), ('merchant_risk', 1.2), ('amount', 'abc'), ('hour', np.nan)])
def test_invalid_features(frame, column, value):
    frame[column] = frame[column].astype(object)
    frame.loc[0, column] = value
    with pytest.raises(ValueError): checker.validate_transactions(frame)


def test_unknown_columns_never_leave_validator(frame):
    frame['account'] = ['123456789012', '123456789013']
    frame['name'] = ['Alice', 'Bob']
    assert list(checker.validate_transactions(frame)) == checker.FEATURES


def test_missing_columns(frame):
    with pytest.raises(ValueError, match='Missing'): checker.validate_transactions(frame.drop(columns='hour'))


def test_empty_frame(frame):
    with pytest.raises(ValueError): checker.validate_transactions(frame.iloc[:0])


def test_row_limit(frame):
    with pytest.raises(ValueError): checker.validate_transactions(pd.concat([frame] * 2501))


def test_csv_limit(tmp_path):
    path = tmp_path / 'large.csv'
    path.write_bytes(b'x' * (2 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match='2 MB'): checker.read_transactions(path)


def test_duplicate_columns(tmp_path):
    path = tmp_path / 'duplicate.csv'
    path.write_text('amount,hour,is_foreign,merchant_risk,amount\n1,2,0,0.1,3')
    with pytest.raises(ValueError, match='Duplicate'): checker.read_transactions(path)


def test_redaction():
    safe = redact_pii('Call +91 98765 43210 email user@example.com account 1234-5678-9012 PAN ABCDE1234F')
    assert '98765' not in safe and 'example.com' not in safe and '1234' not in safe


def test_guardrail_blocks_certainty():
    text, warnings = make_safe('You get guaranteed profit [S1]', {'S1'})
    assert 'withheld' in text and warnings


def test_guardrail_unknown_source():
    text, warnings = make_safe('An unsupported claim [S999]', {'S1'})
    assert '[S999]' not in text and len(warnings) == 2


def test_retrieval_and_no_evidence():
    assert research('diversification concentration')[0]['file'] == '01_diversification.md'
    assert research('zzzzzzzzzzzzzz') == []


def test_threshold_monotonic(frame, model_path):
    low = checker.flag_transactions(frame, 0.2, model_path)
    high = checker.flag_transactions(frame, 0.8, model_path)
    assert low.flagged.sum() >= high.flagged.sum()
    assert low.risk_score.between(0, 1).all()
    assert low.risk_score.iloc[1] > low.risk_score.iloc[0]


def test_demo_market():
    result = market_data('aapl')
    assert result['mode'] == 'synthetic demo' and result['period_change_pct'] == 5
    assert market_data('INFY.NS')['status'] == 'unavailable'


@pytest.mark.parametrize('value', ['../../secret', '', 'AAPL; rm -rf /', 'AAPL MSFT'])
def test_invalid_ticker(value):
    with pytest.raises(ValueError): validate_symbol(value)


def test_message_blocks():
    assert message_text([{'type': 'text', 'text': 'hello'}, {'type': 'thinking'}]) == 'hello\n'


def test_full_demo_and_request_isolation(monkeypatch, model_path):
    import advisoriq.agent as agent
    original = checker.flag_transactions
    monkeypatch.setattr(agent, 'flag_transactions', lambda f, t: original(f, t, model_path))
    first = run_advisor('How does diversification reduce concentration?', use_sample=True)
    second = run_advisor('valuation', use_sample=False)
    assert len(first.transactions) == 10 and second.transactions.empty
    assert first.sources and first.mode == 'offline demo'
    assert 'not personalized financial advice' in first.answer


def test_no_key_import_and_live_fallback(monkeypatch):
    import advisoriq.agent as agent
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    monkeypatch.setattr(agent, 'market_data', lambda *a, **k: {'status': 'unavailable'})
    report = run_advisor('valuation', live=True)
    assert 'deterministic' in report.mode and any('GOOGLE_API_KEY' in w for w in report.warnings)


def test_agent_failure_falls_back(monkeypatch):
    import advisoriq.agent as agent
    monkeypatch.setattr(agent, 'live_ready', lambda: True)
    monkeypatch.setattr(agent, 'market_data', lambda *a, **k: {'status': 'unavailable'})
    def fail(*args): raise RuntimeError('secret-provider-error')
    monkeypatch.setattr(agent, 'invoke_agent', fail)
    report = run_advisor('valuation', live=True)
    assert 'deterministic' in report.answer and 'secret-provider-error' not in str(report)


def test_questions_and_backend():
    for question in ['', '   ', 'x' * 2001]:
        with pytest.raises(ValueError): run_advisor(question)
    with pytest.raises(ValueError): run_advisor('valuation', backend='gemini')


def test_csv_bom(tmp_path):
    path = tmp_path / 'bom.csv'
    path.write_text('amount,hour,is_foreign,merchant_risk\n100,12,0,0.1', encoding='utf-8-sig')
    assert len(checker.read_transactions(path)) == 1
