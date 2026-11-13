# Data handling and limits

- Use synthetic data in the public demo. Gradio receives the raw upload before the application selects numeric features. Uploaded files are cached and eligible for deletion after five minutes on a five-minute cleanup cycle (up to roughly ten minutes under normal operation); no immediate secure deletion is promised.
- The app uses only `amount`, `hour`, `is_foreign` and `merchant_risk`. Extra columns are removed. User filenames/paths are never exposed as agent tools. The local scoring result displays numeric features and row positions.
- The live transaction tool returns aggregate counts only. Questions and source documents can still carry personal details. Regex redaction covers some emails, phone/account-like numbers and PAN patterns; it is not comprehensive and can also over-redact numeric strings.
- LangSmith is off by default. Enable it only when you accept external tracing. Server/provider libraries may have their own operational logs; the local trace intentionally omits raw user content.
- The LLM has no shell, arbitrary URL-fetch, file-writing, database or trading tool. Tickers are explicit and validated. Its research source corpus is controlled by the app maintainer, not an arbitrary upload.
- Prompt instructions, a recursion limit and output regex checks cannot guarantee resistance to prompt injection or hallucination. Citation-ID checks do not validate claim entailment.
- Uploaded CSV size/row limits and the Gradio queue reduce accidental overload. They are not a comprehensive denial-of-service defense. Set authentication for public live-key deployments; this MVP has no per-user billing or rate limiting.
- Only the locally trained joblib artifact is loaded. Never replace it with an untrusted pickle/joblib file: deserialization can execute code.
- Development server binds to localhost by default. Set HOST=0.0.0.0 only when intentionally hosting it. Keep keys in environment variables. Do not commit `.env`.
- If a key is exposed, revoke it with the provider. Removing the current file from Git does not remove the secret from repository history.
