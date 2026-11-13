"""Reproducible synthetic classifier. No real-world fraud claim."""
import csv
import io
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from .config import FEATURES, MODEL_PATH, MAX_BYTES, MAX_ROWS


def validate_transactions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or len(frame) > MAX_ROWS:
        raise ValueError(f'Upload between 1 and {MAX_ROWS} transactions.')
    missing = set(FEATURES) - set(frame.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    # Allowlist: names, account IDs, descriptions and labels never reach the model.
    safe = frame[FEATURES].copy()
    for name in FEATURES:
        safe[name] = pd.to_numeric(safe[name], errors='coerce')
    if not np.isfinite(safe.to_numpy(dtype=float)).all():
        raise ValueError('All four feature columns must contain finite numbers with no blanks.')
    if not safe.amount.between(0, 1e9).all():
        raise ValueError('amount must be between 0 and 1,000,000,000.')
    if not (safe.hour.between(0, 23) & (safe.hour % 1 == 0)).all():
        raise ValueError('hour must be an integer from 0 to 23.')
    if not safe.is_foreign.isin([0, 1]).all():
        raise ValueError('is_foreign must be 0 or 1.')
    if not safe.merchant_risk.between(0, 1).all():
        raise ValueError('merchant_risk must be between 0 and 1.')
    return safe.reset_index(drop=True)


def read_transactions(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() != '.csv':
        raise ValueError('Please upload a CSV file.')
    with path.open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('CSV must be at most 2 MB.')
    try:
        text = raw.decode('utf-8-sig')
        header = next(csv.reader(io.StringIO(text)))
        if len(header) != len(set(header)):
            raise ValueError('Duplicate CSV column names are not allowed.')
        frame = pd.read_csv(io.StringIO(text), nrows=MAX_ROWS + 1)
    except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError, StopIteration) as exc:
        raise ValueError('Could not parse this UTF-8 CSV.') from exc
    return validate_transactions(frame)


def synthetic_data(n=4000, seed=42):
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({
        'amount': np.round(rng.lognormal(6.5, 1.5, n), 2),
        'hour': rng.integers(0, 24, n),
        'is_foreign': rng.binomial(1, 0.15, n),
        'merchant_risk': np.round(rng.beta(2, 5, n), 3),
    })
    logit = (-4 + 2.5 * (frame.amount > 4000) + 1.5 * frame.is_foreign
             + 4 * frame.merchant_risk + 1.3 * (frame.hour < 5))
    frame['label'] = rng.binomial(1, 1 / (1 + np.exp(-logit)))
    return frame


def train(path=MODEL_PATH):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
    frame = synthetic_data()
    X_train, X_test, y_train, y_test = train_test_split(
        frame[FEATURES], frame.label, test_size=0.25, stratify=frame.label, random_state=42)
    model = RandomForestClassifier(n_estimators=120, max_depth=7, min_samples_leaf=8,
                                   class_weight='balanced', random_state=42, n_jobs=1)
    model.fit(X_train, y_train)
    scores = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
    pred = scores >= 0.5
    metrics = { 'dataset': 'synthetic only; not evidence of real-world fraud performance',
        'seed': 42, 'train_rows': len(X_train), 'test_rows': len(X_test), 'threshold': 0.5,
        'positive_test_rows': int(y_test.sum()),
        'precision': float(precision_score(y_test, pred, zero_division=0)),
        'recall': float(recall_score(y_test, pred, zero_division=0)),
        'f1': float(f1_score(y_test, pred, zero_division=0)),
        'roc_auc': float(roc_auc_score(y_test, scores)),
        'confusion_matrix': confusion_matrix(y_test, pred).tolist() }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model, 'features': FEATURES, 'metrics': metrics}, path)
    return metrics


def flag_transactions(frame: pd.DataFrame, threshold=0.5, path=MODEL_PATH):
    if not 0 <= threshold <= 1:
        raise ValueError('Threshold must be between 0 and 1.')
    safe = validate_transactions(frame)
    if not Path(path).exists():
        raise ValueError('Checker not built. Run: python -m advisoriq.setup')
    # Only load this application's locally trained artifact, never user-uploaded pickle files.
    artifact = joblib.load(path)
    scores = artifact['model'].predict_proba(safe)[:, list(artifact['model'].classes_).index(1)]
    result = safe.copy()
    result.insert(0, 'row', np.arange(1, len(result) + 1))
    result['risk_score'] = np.round(scores, 4)
    result['flagged'] = scores >= threshold
    def indicators(row):
        signals = []
        if row.amount > 4000: signals.append('large amount in demo units')
        if row.hour < 5: signals.append('overnight hour')
        if row.is_foreign: signals.append('foreign transaction')
        if row.merchant_risk >= 0.5: signals.append('elevated merchant input')
        return '; '.join(signals) or 'no simple rule indicator'
    result['review_indicators'] = safe.apply(indicators, axis=1)
    return result
