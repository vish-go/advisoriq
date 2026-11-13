"""Offline, reproducible evaluation. Retrieval hit rate is not RAGAS faithfulness."""
import json
from advisoriq.checker import train
from advisoriq.rag import research
from advisoriq.config import ROOT

CASES = [
    ('How does diversification reduce concentration risk?', '01_diversification.md'),
    ('Does a low price to earnings ratio imply good valuation?', '02_valuation.md'),
    ('How do precision and recall affect transaction fraud review?', '03_transaction_review.md'),
    ('Is a daily closing price an executable quote?', '04_market_data.md'),
    ('What happens to false alarms when lowering a score threshold?', '03_transaction_review.md'),
    ('Should I compare company margins debt and cash flows?', '02_valuation.md'),
    ('How should I check currency timezone and stale observations?', '04_market_data.md'),
    ('Can different sector holdings still have shared risks?', '01_diversification.md'),
]


def main():
    results = []
    for question, expected in CASES:
        hits = research(question, k=3)
        files = [s['file'] for s in hits]
        results.append({'question': question, 'expected': expected, 'retrieved': files,
                        'hit_at_1': bool(files and files[0] == expected), 'hit_at_3': expected in files})
    report = {'checker': train(), 'retrieval': {
        'benchmark': '8 developer-authored questions over 4 bundled notes; smoke benchmark, not independent validation',
        'hit_at_1': sum(r['hit_at_1'] for r in results) / len(results),
        'hit_at_3': sum(r['hit_at_3'] for r in results) / len(results), 'cases': results},
        'generation': 'Not evaluated by an LLM judge; no RAGAS or faithfulness score claimed.'}
    path = ROOT / 'reports' / 'evaluation.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
