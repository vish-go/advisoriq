"""Contract tests: external services replaced with explicit fixtures, no network or keys."""
import pandas as pd
from advisoriq.market import market_data


def test_market_provider_timestamp(monkeypatch):
    import yfinance
    class FakeTicker:
        history_metadata = {'currency': 'INR'}
        def history(self, **kwargs):
            return pd.DataFrame({'Close': [100.0, 110.0]}, index=pd.to_datetime(['2026-01-01', '2026-01-02']))
    monkeypatch.setattr(yfinance, 'Ticker', lambda s: FakeTicker())
    result = market_data('INFY.NS', demo=False)
    assert result['currency'] == 'INR' and result['period_change_pct'] == 10
    assert '2026-01-02' in result['as_of']


def test_market_outage(monkeypatch):
    import yfinance
    def fail(s): raise RuntimeError('sensitive')
    monkeypatch.setattr(yfinance, 'Ticker', fail)
    result = market_data('AAPL', demo=False)
    assert result['status'] == 'unavailable' and 'sensitive' not in str(result)


def test_chroma_local_contract(tmp_path):
    from langchain_core.embeddings import Embeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    class FixedEmbeddings(Embeddings):
        def embed_documents(self, texts): return [[1.0, 0.0, 0.0] for _ in texts]
        def embed_query(self, text): return [1.0, 0.0, 0.0]
    store = Chroma(collection_name='contract-test', persist_directory=str(tmp_path), embedding_function=FixedEmbeddings())
    store.add_documents([Document(page_content='evidence', metadata={'source_id': 'S1', 'file': 'note.md'})], ids=['S1'])
    assert store.similarity_search('query', k=1)[0].metadata['source_id'] == 'S1'


def test_agent_executes_tools_with_fake_model(monkeypatch):
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    import langchain_google_genai
    from advisoriq.agent import invoke_agent
    class FakeModel(BaseChatModel):
        @property
        def _llm_type(self): return 'test-fixture'
        def bind_tools(self, tools, **kwargs): return self
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            if any(getattr(m, 'type', '') == 'tool' for m in messages):
                message = AIMessage(content='Diversification evidence [S1].')
            else:
                message = AIMessage(content='', tool_calls=[
                    {'name': 'Research', 'args': {'query': 'diversification'}, 'id': '1', 'type': 'tool_call'},
                    {'name': 'MarketData', 'args': {}, 'id': '2', 'type': 'tool_call'},
                    {'name': 'CheckTransactions', 'args': {}, 'id': '3', 'type': 'tool_call'}])
            return ChatResult(generations=[ChatGeneration(message=message)])
    monkeypatch.setenv('GEMINI_MODEL', 'test-fixture')
    monkeypatch.setattr(langchain_google_genai, 'ChatGoogleGenerativeAI', lambda **kwargs: FakeModel())
    sources, events = [], []
    result = invoke_agent('diversification', {'status': 'unavailable'}, pd.DataFrame(), sources, 'local', events)
    assert '[S1]' in result and sources
    assert {e['step'] for e in events} == {'Agent: Research', 'Agent: MarketData', 'Agent: CheckTransactions'}
