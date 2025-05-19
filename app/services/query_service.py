import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from pathlib import Path
import cohere
import os
from dotenv import load_dotenv

# Load environment and API keys
load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))

#  Load MiniLM model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

#  Load FAISS indexes and metadata (MedlinePlus + OpenFDA)
medline_index = faiss.read_index("E:/MiiHA/app/db/miiha_medline.index")
openfda_index = faiss.read_index("E:/MiiHA/app/db/openfda_all_drugs.index")

with open("E:/MiiHA/app/data/metadata/medline_metadata.json", "r", encoding="utf-8") as f:
    medline_metadata = json.load(f)

with open("E:/MiiHA/app/data/metadata/openfda_all_drugs_metadata.json", "r", encoding="utf-8") as f:
    openfda_metadata = json.load(f)

# 🔍 Full RAG Query Function
def query_rag(query: str, top_k: int = 15):
    # 1. Embed query
    query_vector = model.encode([query])[0].astype("float32")

    # 2. Search FAISS indexes separately
    medline_scores, medline_indices = medline_index.search(np.array([query_vector]), top_k)
    openfda_scores, openfda_indices = openfda_index.search(np.array([query_vector]), top_k)

    # 3. Collect results from both sources
    combined_chunks = []

    for i in medline_indices[0]:
        if i < len(medline_metadata):
            chunk = medline_metadata[i]
            chunk["source"] = "MedlinePlus"
            combined_chunks.append(chunk)

    for i in openfda_indices[0]:
        if i < len(openfda_metadata):
            chunk = openfda_metadata[i]
            chunk["source"] = "OpenFDA"
            combined_chunks.append(chunk)

    # 4. Rerank combined chunks using Cohere
    reranked_chunks = rerank_with_cohere(query, combined_chunks, top_n=3)

    # 5. Generate answer from reranked top-3
    answer = generate_answer(query, reranked_chunks)

    # 6. Return result
    return {
        "query": query,
        "answer": answer,
        "sources": reranked_chunks
    }

#  Cohere Rerank
def rerank_with_cohere(query: str, raw_chunks: list, top_n: int = 3):
    documents = []

    # Choose text depending on source
    for doc in raw_chunks:
        if doc["source"] == "MedlinePlus":
            documents.append(doc.get("title", ""))
        elif doc["source"] == "OpenFDA":
            documents.append(doc.get("purpose", "") or doc.get("drug_name", ""))

    rerank_results = co.rerank(
        query=query,
        documents=documents,
        top_n=top_n,
        model="rerank-english-v2.0"
    ).results

    return [raw_chunks[result.index] for result in rerank_results]

# 🗣️ Cohere Generate
def generate_answer(query: str, context_docs: list):
    context_texts = []

    for doc in context_docs:
        if doc["source"] == "MedlinePlus":
            context_texts.append(doc.get("title", ""))
        elif doc["source"] == "OpenFDA":
            context_texts.append(doc.get("purpose", "") or doc.get("drug_name", ""))

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

