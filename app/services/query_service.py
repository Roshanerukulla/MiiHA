import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from app.config.paths import (
    MEDLINE_INDEX_PATH,
    OPENFDA_INDEX_PATH,
    MEDLINE_METADATA_PATH,
    OPENFDA_METADATA_PATH
)
import cohere
import os

# Load environment and API keys
load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))

# Load MiniLM model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Load FAISS indexes and metadata
medline_index = faiss.read_index(str(MEDLINE_INDEX_PATH))
openfda_index = faiss.read_index(str(OPENFDA_INDEX_PATH))

with open(MEDLINE_METADATA_PATH, "r", encoding="utf-8") as f:
    medline_metadata = json.load(f)

with open(OPENFDA_METADATA_PATH, "r", encoding="utf-8") as f:
    openfda_metadata = json.load(f)

# 🔍 Full RAG Query Function
def query_rag(query: str, top_k: int = 15):
    query_vector = model.encode([query])[0].astype("float32")

    medline_scores, medline_indices = medline_index.search(np.array([query_vector]), top_k)
    openfda_scores, openfda_indices = openfda_index.search(np.array([query_vector]), top_k)

    combined_chunks = []

    for i in medline_indices[0]:
        if 0 <= i < len(medline_metadata):
            chunk = dict(medline_metadata[i])
            chunk["source"] = "MedlinePlus"
            combined_chunks.append(chunk)

    for i in openfda_indices[0]:
        if 0 <= i < len(openfda_metadata):
            chunk = dict(openfda_metadata[i])
            chunk["source"] = "OpenFDA"
            combined_chunks.append(chunk)

    reranked_chunks = rerank_with_cohere(query, combined_chunks, top_n=3)
    answer = generate_answer(query, reranked_chunks)

    return {
        "query": query,
        "answer": answer,
        "sources": reranked_chunks
    }

# 🔁 Cohere Rerank
def rerank_with_cohere(query: str, raw_chunks: list, top_n: int = 3):
    documents = []

    for doc in raw_chunks:
        if doc["source"] == "MedlinePlus":
            documents.append(doc.get("title", ""))
        elif doc["source"] == "OpenFDA":
            documents.append(doc.get("purpose", "") or doc.get("drug_name", ""))

    rerank_results = co.rerank(
        query=query,
        documents=documents,
        top_n=top_n,
        model="rerank-english-v3.0"
    ).results

    return [raw_chunks[result.index] for result in rerank_results]

# 🧠 Generate Answer
def generate_answer(query: str, context_docs: list):
    context_texts = []

    for doc in context_docs:
        if doc["source"] == "MedlinePlus":
            context_texts.append(f"[MedlinePlus] {doc.get('title', '')}")
        elif doc["source"] == "OpenFDA":
            context_texts.append(f"[OpenFDA] {doc.get('purpose', '') or doc.get('drug_name', '')}")

    context_text = "\n\n".join(context_texts)

    prompt = f"""
You are a helpful, medically accurate health assistant named MIIHA.

Use the provided context below to answer the user's question if possible.
If the context is not relevant or sufficient, use your general medical knowledge to provide the best answer while being careful and factual.

Context:
{context_text}

Question:
{query}

Answer:"""

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=300,
        temperature=0.5
    )

    return response.generations[0].text.strip()
