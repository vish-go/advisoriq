"""Interface contract smoke checks, without a browser or external services."""
import pytest


def test_interface_and_callback(monkeypatch):
    for key in ('ALL_PROXY', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'http_proxy', 'https_proxy'):
        monkeypatch.delenv(key, raising=False)
    import app
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from advisoriq.checker import train
    from advisoriq.config import MODEL_PATH
    if not MODEL_PATH.exists():
        train()
    ui = app.create_app()
    mounted = app.gr.mount_gradio_app(FastAPI(), ui, path='/')
    client = TestClient(mounted)
    assert client.get('/').status_code == 200
    assert client.get('/config').status_code == 200
    result = app.advise('diversification and valuation', 'AAPL', None, True, False, 0.5, 'local')
    assert len(result) == 6 and len(result[1]) == 10 and len(result[3]) == 10
    assert 'offline demo' in result[-1]
    with pytest.raises(app.gr.Error):
        app.advise('', 'AAPL', None, False, False, 0.5, 'local')
    outputs = [d for d in ui.fns.values() if getattr(d.fn, '__name__', '') == 'advise'][0].outputs
    for component, value in zip(outputs, result):
        component.postprocess(value)
