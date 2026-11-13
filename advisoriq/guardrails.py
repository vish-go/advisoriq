"""Defense in depth, not a claim of complete PII or hallucination detection."""
import re

DISCLAIMER = 'Educational research only; not personalized financial advice. Flagged transactions require human review and are not proof of fraud.'


def redact_pii(text: str) -> str:
    text = re.sub(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', '[EMAIL]', text)
    text = re.sub(r'(?<!\w)\+?\d(?:[ -]?\d){9,18}(?!\w)', '[NUMBER]', text)
    text = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', '[PAN]', text, flags=re.I)
    return text


def make_safe(answer: str, source_ids: set[str]) -> tuple[str, list[str]]:
    warnings = []
    if re.search(r'guaranteed\s+(?:return|profit)|can[’\']?t lose|risk[- ]free profit', answer, re.I):
        answer = 'The generated response contained an unsupported certainty claim and was withheld. Review the evidence cards and consult a qualified adviser.'
        warnings.append('Unsupported certainty claim blocked.')
    citations = set(re.findall(r'\[(S\d+)\]', answer))
    unknown = citations - source_ids
    if unknown:
        answer = re.sub(r'\[(S\d+)\]', lambda m: m[0] if m[1] in source_ids else '[unverified citation removed]', answer)
        warnings.append('Unknown source identifiers removed.')
    if not citations.intersection(source_ids):
        warnings.append('No verified document citation in answer; treat as weakly supported.')
    answer = redact_pii(answer)
    return answer + '\n\n---\n' + DISCLAIMER, warnings
