from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
DATA = ROOT / 'data'
MODEL_PATH = ROOT / 'models' / 'checker.joblib'
INDEX_PATH = ROOT / 'chroma_store'
MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 5000
FEATURES = ['amount', 'hour', 'is_foreign', 'merchant_risk']


def live_ready():
    return bool(os.getenv('GOOGLE_API_KEY')) and bool(os.getenv('GEMINI_MODEL'))
