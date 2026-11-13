"""Local TF-IDF baseline plus optional Gemini embeddings / Chroma index."""
from pathlib import Path
import hashlib
import json
from functools import lru_cache
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .config import DATA, INDEX_PATH
from .guardrails import redact_pii


def load_chunks(directory=DATA / 'docs'):
    chunks = []
    for path in sorted(Path(directory).glob('*.md')):
        text = path.read_text(encoding='utf-8')
        for offset in range(0, len(text), 1000):
            passage = text[max(0, offset - 120):offset + 1000].strip()
            if passage:
                chunks.append({'id': f'S{len(chunks) + 1}', 'file': path.name,
                               'text': redact_pii(passage)})
    if not chunks:
        raise ValueError('No research documents. Add .md files under data/docs/.')
    return chunks


@lru_cache(maxsize=1)
def local_index():
    chunks = load_chunks()
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([c['text'] for c in chunks])
    return chunks, vectorizer, matrix


def research(query: str, backend='local', k=3):
    query = redact_pii(query[:2000])
    if backend == 'gemini':
        manifest_path = INDEX_PATH / 'manifest.json'
        if not manifest_path.exists():
            raise ValueError('Gemini research index not built. Run: python -m advisoriq.setup --embeddings')
        manifest = json.loads(manifest_path.read_text())
        chunks = load_chunks()
        fingerprint = hashlib.sha256(json.dumps(chunks, sort_keys=True).encode()).hexdigest()
        if manifest['fingerprint'] != fingerprint:
            raise ValueError('Documents changed; rebuild the Gemini index.')
        store = gemini_store(manifest['collection'], manifest['model'])
        docs = store.similarity_search(query, k=k)
        return [{'id': d.metadata['source_id'], 'file': d.metadata['file'], 'text': d.page_content} for d in docs]
    chunks, vectorizer, matrix = local_index()
    scores = cosine_similarity(vectorizer.transform([query]), matrix)[0]
    return [{**chunks[i], 'similarity': round(float(scores[i]), 4)}
            for i in scores.argsort()[::-1][:k] if scores[i] > 0.025]


def gemini_store(collection, model):
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    return Chroma(collection_name=collection, persist_directory=str(INDEX_PATH),
                  embedding_function=GoogleGenerativeAIEmbeddings(model=model))


def build_library():
    from langchain_core.documents import Document
    chunks = load_chunks()
    fingerprint = hashlib.sha256(json.dumps(chunks, sort_keys=True).encode()).hexdigest()
    model = os.getenv('EMBEDDING_MODEL', 'models/gemini-embedding-001')
    collection = 'research-' + hashlib.sha256((fingerprint + model).encode()).hexdigest()[:16]
    store = gemini_store(collection, model)
    store.add_documents([Document(page_content=c['text'], metadata={'source_id': c['id'], 'file': c['file']})
                         for c in chunks], ids=[c['id'] for c in chunks])
    (INDEX_PATH / 'manifest.json').write_text(json.dumps({'collection': collection, 'model': model,
                                                        'fingerprint': fingerprint}, indent=2))
    return len(chunks)
