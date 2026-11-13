# Verification record

Verified in this workspace with Python 3.12.14 and the recorded dependency snapshot:

- `pip check`: no broken requirements.
- `python -m advisoriq.setup`: trained and saved the synthetic model.
- `python evaluate.py`: generated the included held-out classifier and retrieval reports.
- `python -m pytest -q`: **35 tests passed**.
- Gradio app construction, HTTP home/config routes, demo callback and all output component serialization passed.
- LangChain agent completed a three-tool loop with a controlled fake chat model.
- Chroma add/query contract passed with a deterministic test embedding implementation.
- Market provider behavior passed with mocked dated observations and outage cases.

Not verified here:

- Authenticated Gemini generation or embedding API calls: no user API key supplied.
- Real Yahoo market requests: provider contract tested with fixtures.
- Browser-rendered layout: automated Chromium could not launch under this workspace's process restrictions.
- Render deployment, Docker build, GitHub-hosted CI: configuration supplied, not run remotely.

This record deliberately separates local behavior from external-service validation. Use the README's live configuration steps and confirm the mode label before claiming the integrations are deployed and working on your account.
