import argparse
import json
from .checker import train
from .rag import build_library
from .config import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--embeddings', action='store_true')
    args = parser.parse_args()
    metrics = train()
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / 'checker_metrics.json').write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    if args.embeddings:
        print(f'Indexed {build_library()} chunks with Gemini embeddings.')
    print('Setup complete. Start with: python app.py')


if __name__ == '__main__':
    main()
