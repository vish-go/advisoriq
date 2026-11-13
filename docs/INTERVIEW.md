# Internship presentation guide

## Three-minute demonstration

**0:00–0:30 — Problem:** “AdvisorIQ puts document evidence, market observations and transaction review in one inspectable workspace. It supports an analyst; it does not make or execute investment decisions.”

**0:30–1:15 — Run:** Start the offline sample, generate a brief, point out the demo label and click Sources. Explain that citations map to retrieved chunks. A current company valuation cannot be inferred from these general notes.

**1:15–1:50 — Model:** Open Transaction review. Change the threshold, rerun and compare flags. Explain the synthetic dataset, held-out split, false-positive tradeoff and why scores are not real fraud probabilities.

**1:50–2:30 — Engineering:** Show Run trace, then tests/ and the workflow. Demonstrate one invalid CSV or missing-provider fallback. Explain why raw transaction records are kept away from the model.

**2:30–3:00 — Tradeoffs:** If your live credentials have been tested, show the Gemini tool trace. Explain why deterministic preflight checks and a fallback improve reliability. Name the next improvement you can defend: independent evaluation on date-versioned company filings.

## Resume wording

Use only capabilities you have actually run and can explain:

“Built AdvisorIQ, a Python research copilot with document retrieval, synthetic transaction classification, a Gradio dashboard and automated tests; implemented request-scoped data handling, source tracking and provider-failure fallbacks.”

After validating Gemini and Chroma with your own credentials, add:

“Integrated a bounded LangChain/Gemini tool-calling agent with Gemini embeddings and Chroma, exposing market observations and aggregate transaction checks.”

Do not claim production deployment until deployed, real-time quotes when using daily history, real-world fraud accuracy, portfolio optimization, RAGAS evaluation, or complete PII protection. You can explain that AI assisted implementation and describe the pieces you validated and changed yourself.

## Questions to prepare

1. Why compare TF-IDF and embeddings? Lexical baseline versus semantic matching, latency, cost and relevance thresholds.
2. Why a random forest? Useful nonlinear baseline for tabular features, but synthetic data limits validity.
3. What does the confusion matrix mean? Explain the 196 false positives and 40 missed positives in the saved synthetic test set.
4. Why not upload a bank statement directly? The schema needs engineered features and merchant-risk input; extraction and normalization are separate problems.
5. What makes this an agent? The live LLM decides how to call three bounded tools; offline mode is deliberately a deterministic workflow.
6. Why precompute some outputs? Mandatory checks remain reliable even if the agent skips a tool or errors.
7. Are citations proof? No. ID validation establishes provenance, not that a claim is entailed by a passage.
8. What can leak? Free text and document content can contain identifiers regex misses; tracing is opt-in, uploaded cache has delayed cleanup.
9. What would production need? Real authorized data, independent evaluation, calibrated thresholds, authentication, rate limits, tenant isolation, operational monitoring and a domain-specific compliance review.
10. What would you improve first? Pick one measurable improvement and demonstrate its before/after behavior.

## Five study sessions

1. Run the app; explain the CSV schema and add one validation test.
2. Trace one row through the random forest and compute precision/recall by hand.
3. Add one original research document and an evaluation question; inspect retrieval before and after.
4. Configure Gemini; trace all three tools and trigger a controlled fallback.
5. Record the demo; rehearse tradeoffs; push a small improvement with a meaningful commit.
