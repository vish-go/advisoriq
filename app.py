"""Gradio entrypoint; no credentials or network calls at import time."""
import os
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'false')
import html
import pandas as pd
import gradio as gr
from advisoriq.agent import run_advisor
from advisoriq.config import ROOT, DATA

CSS = '''
.gradio-container {max-width:1200px!important;margin:auto!important;font-family:Inter,system-ui,sans-serif!important;}
#hero {padding:28px 30px;background:linear-gradient(120deg,#102a43,#123f48);border-radius:18px;color:#f1f8fa;margin:12px 0 22px;}
#hero h1 {color:white;font-size:36px;letter-spacing:-1.2px;margin:8px 0;}
#hero p {color:#d3e8ec;max-width:760px;line-height:1.6;}
#eyebrow {color:#89dbc8;font-size:12px;letter-spacing:2px;font-weight:700;}
#brief {min-height:250px;}
'''


def advise(question, symbol, csv_file, sample, live, threshold, backend):
    try:
        report = run_advisor(question, symbol, csv_file, sample, live, threshold, backend)
        cards = '\n\n'.join(f"### [{s['id']}] {html.escape(s['file'])}\n{html.escape(s['text'])}" for s in report.sources)
        warnings = '\n'.join('- ' + w for w in report.warnings)
        status = f'**Mode:** {report.mode} · **Evidence excerpts:** {len(report.sources)} · **Transactions:** {len(report.transactions)}'
        if warnings:
            status += '\n\n' + warnings
        chart = pd.DataFrame(report.market.get('history', []), columns=['session', 'close'])
        return report.answer, report.transactions, cards or 'No document evidence retrieved.', chart, report.events, status
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    except Exception as exc:
        raise gr.Error('Request failed. Check setup and server logs, then retry.') from exc


def create_app():
    with gr.Blocks(title='AdvisorIQ | Research workspace', analytics_enabled=False,
                   delete_cache=(300, 300)) as demo:
        gr.HTML('''<section id="hero"><div id="eyebrow">ADVISORIQ / RESEARCH WORKSPACE</div>
        <h1>Evidence before decisions.</h1><p>Explore market observations, trace answers to research notes,
        and bring unusual transactions into focus. Built for transparent, human-reviewed analysis.</p></section>''')
        with gr.Row():
            with gr.Column(scale=4):
                gr.Markdown('### Build your research brief')
                question = gr.Textbox(label='Research question', lines=4,
                    value='How should I evaluate concentration and valuation risk before buying Apple? Review my transactions too.')
                symbol = gr.Textbox(label='Market ticker', value='AAPL', info='Explicit ticker avoids ambiguous company-name matching.')
                upload = gr.File(label='Transactions CSV (optional · max 2 MB)', file_types=['.csv'], type='filepath')
                sample = gr.Checkbox(value=True, label='Use synthetic sample when no CSV is uploaded')
                with gr.Accordion('Research settings', open=False):
                    live = gr.Checkbox(value=False, label='Live market + optional Gemini agent',
                        info='Live mode sends the redacted question and research excerpts to Gemini if configured. Use no sensitive personal data.')
                    backend = gr.Dropdown(['local', 'gemini'], value='local', label='Retrieval: local TF-IDF or Gemini / Chroma')
                    threshold = gr.Slider(0, 1, value=0.5, step=0.05, label='Transaction review threshold')
                submit = gr.Button('Generate research brief', variant='primary')
                gr.File(value=str(DATA / 'sample_transactions.csv'), label='Download sample CSV', interactive=False)
                gr.Markdown('**CSV columns:** `amount`, `hour`, `is_foreign`, `merchant_risk`. Extra columns are discarded. '
                            'Use synthetic data for public demos. Uploaded files may remain in the Gradio cache for up to 10 minutes.')
            with gr.Column(scale=7):
                status = gr.Markdown('**Offline demo ready** · No API key required · Sample prices are synthetic')
                with gr.Tabs():
                    with gr.Tab('Research brief'):
                        answer = gr.Markdown('Your evidence-backed brief will appear here.', elem_id='brief', sanitize_html=True)
                    with gr.Tab('Transaction review'):
                        gr.Markdown('Scores are **not calibrated fraud probabilities**. Rule indicators are separate from model explanations. '
                                    'Amounts must use a consistent unit; the synthetic model is not currency-aware.')
                        transactions = gr.Dataframe(interactive=False, wrap=True)
                    with gr.Tab('Sources'):
                        sources = gr.Markdown('Retrieved excerpts will appear here.', sanitize_html=True)
                    with gr.Tab('Market history'):
                        chart = gr.LinePlot(x='session', y='close', x_title='Observation', y_title='Adjusted close / demo units',
                                            title='Daily observations · inspect the brief for timestamp and currency')
                    with gr.Tab('Run trace'):
                        events = gr.JSON(label='Request-local tool events (no raw CSV or question logging)')
        submit.click(advise, [question, symbol, upload, sample, live, threshold, backend],
                     [answer, transactions, sources, chart, events, status], api_name=False, concurrency_limit=2)
        gr.Markdown('AdvisorIQ is an educational portfolio project. It does not execute trades or replace a qualified financial adviser.')
    return demo


if __name__ == '__main__':
    username, password = os.getenv('APP_USERNAME'), os.getenv('APP_PASSWORD')
    if bool(username) != bool(password):
        raise RuntimeError('Set both APP_USERNAME and APP_PASSWORD, or neither.')
    create_app().queue(max_size=12).launch(server_name=os.getenv('HOST', '127.0.0.1'),
        server_port=int(os.getenv('PORT', '7860')), css=CSS, theme=gr.themes.Soft(primary_hue='teal'),
        auth=(username, password) if username and password else None,
        max_file_size='2mb', show_error=False)
