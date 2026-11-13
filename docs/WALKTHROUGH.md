# Your step-by-step guide

## 1. Run it before changing it

Follow the operating-system commands in README.md. Use Python 3.12, not an untested newer version. Run setup once; it creates `models/checker.joblib`. Start `app.py`, open localhost:7860 and generate the default brief.

Expected: an offline-demo mode label, clearly fictional AAPL prices, research citations, transaction flags, a chart and a short run trace. No API key is needed. A source citation such as `[S1]` should correspond to an excerpt in Sources.

## 2. Understand the input

Open `data/sample_transactions.csv`. Each row has four numeric features. `amount` has no built-in currency; `merchant_risk` is already supplied. Upload a copy with an invalid hour such as 25: the app should reject it. Upload a valid file with an extra name column: the model and displayed results must omit that column.

Learn: validation, pandas dataframes, allowlisting, finite-number checks and bounded file reads.

## 3. Understand the model

Read `advisoriq/checker.py` in this order: `synthetic_data`, `train`, `validate_transactions`, `flag_transactions`.

The generator uses a seeded probabilistic rule to create synthetic labels, not manually labeled fraud. The split happens before model training. A random forest estimates class scores; a threshold turns those into review flags. The model's output is not a calibrated probability of real fraud. The rule indicator column is a separate descriptive heuristic, not an explanation of the random forest.

Run `python evaluate.py` and inspect the confusion matrix. At the default threshold this run has 115 true positives, 196 false positives, 40 false negatives and 649 true negatives. Explain why recall can be relatively high while precision is low. Do not tune on this held-out set and then present the same set as independent validation.

## 4. Understand retrieval

Read `advisoriq/rag.py`. Documents are split into overlapping text chunks and retain source metadata. Offline TF-IDF gives a cheap, repeatable lexical baseline; it does not understand every synonym. A similarity floor means unrelated text can return no sources.

The optional Gemini backend embeds chunks and stores vectors in Chroma. A manifest records the model and document fingerprint. A changed document requires reindexing. Embedding retrieval currently returns nearest neighbors without a relevance threshold, so irrelevant nearest neighbors remain a limitation.

Try a relevant question and then nonsense text. Inspect the difference. The included eight-question retrieval evaluation measures which document appears, not whether a generated answer is true.

## 5. Understand orchestration

Read `advisoriq/agent.py`:

1. Reject oversized/empty questions and invalid tickers.
2. Redact common structured identifiers in the question.
3. Validate CSV and score its allowlisted features locally.
4. Obtain synthetic or external market observations.
5. Retrieve source excerpts.
6. Prepare a deterministic fallback report.
7. If configured, run a bounded Gemini agent with three tools.
8. Check unsupported certainty phrases and source IDs.
9. Return structured results to Gradio.

Each request has separate source, transaction and event objects. The model cannot read an arbitrary path or place a trade. The CheckTransactions tool exposes only row/flag counts. Agent prompts and regex checks are helpful boundaries, not guarantees of safe or truthful outputs.

## 6. Enable the real integrations

Copy `.env.example` to `.env`. Add your Gemini API key and a currently supported model ID. Restart the server, enable live mode, and first use local retrieval to isolate the chat-model configuration. Confirm the mode says `Gemini agent`; if it says deterministic summary, read the warning.

Then build the embedding index and select Gemini retrieval. Run a question whose answer exists in a document. Check that Sources contains the cited excerpts and that the Run trace includes agent tool calls. Enable LangSmith only with synthetic/non-sensitive prompts and informed consent to tracing.

A missing key, expired model ID, quota error or provider outage must not become an invented answer. The fallback and warning should be visible.

## 7. Prepare the internship demo

Run the test suite, read the evaluation report, and follow the 3-minute script in INTERVIEW.md. Record a short video after enabling and verifying the live integration on your account. Keep the no-key demo for reliable interviews. Never show `.env` while recording.

## File map

| File | Responsibility |
|---|---|
| `app.py` | Gradio layout and request adapter |
| `advisoriq/config.py` | Paths, limits and environment |
| `advisoriq/checker.py` | Validation, synthetic model, scoring |
| `advisoriq/rag.py` | Chunking, local retrieval, Gemini/Chroma |
| `advisoriq/market.py` | Ticker validation, provider handling |
| `advisoriq/guardrails.py` | Partial PII masking, output checks |
| `advisoriq/agent.py` | Deterministic workflow and optional agent |
| `advisoriq/setup.py` | Model and optional index generation |
| `evaluate.py` | Reproducible classifier/retrieval evaluation |
| `tests/` | Validation, isolation, fallback, integration contracts |
| `.github/workflows/ci.yml` | Automated checks |
