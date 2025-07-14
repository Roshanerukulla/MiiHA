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

# Optional DrugBank
try:
    from app.config.paths import DRUGBANK_INDEX_PATH, DRUGBANK_METADATA_PATH
    drugbank_index = faiss.read_index(str(DRUGBANK_INDEX_PATH))
    with open(DRUGBANK_METADATA_PATH, "r", encoding="utf-8") as f:
        drugbank_metadata = json.load(f)
except Exception as e:
    print("⚠️ DrugBank index or metadata not loaded:", e)
    drugbank_index = None
    drugbank_metadata = []

def simulate_rag_chunk_quality(chunks):
    return 0.6 if len(chunks) >= 2 else 0.2

# Full RAG Query Function with Tone & Fallback

def query_rag(query: str, chat_history: list = None, top_k: int = 15, tone: str = "friendly"):
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

    if drugbank_index:
        try:
            db_scores, db_indices = drugbank_index.search(np.array([query_vector]), top_k)
            for i in db_indices[0]:
                if 0 <= i < len(drugbank_metadata):
                    chunk = dict(drugbank_metadata[i])
                    chunk["source"] = "DrugBank"
                    combined_chunks.append(chunk)
        except Exception as e:
            print(" DrugBank query failed:", e)

    reranked_chunks = rerank_with_cohere(query, combined_chunks, top_n=3)

    use_rag = simulate_rag_chunk_quality(reranked_chunks) > 0.4
    answer = generate_answer(query, reranked_chunks if use_rag else [], chat_history, tone, use_rag)

    safe_sources = []
    for doc in reranked_chunks:
        if doc["source"] == "DrugBank":
            safe_sources.append({
                "title": doc.get("title"),
                "url": doc.get("url"),
                "source": "DrugBank",
                "note": "Description hidden due to DrugBank license. Visit link for details."
            })
        else:
            safe_sources.append(doc)

    return {
        "query": query,
        "answer": answer,
        "sources": safe_sources if use_rag else []
    }

def rerank_with_cohere(query: str, raw_chunks: list, top_n: int = 3):
    documents = []
    for doc in raw_chunks:
        if doc["source"] == "MedlinePlus":
            documents.append(doc.get("title", ""))
        elif doc["source"] == "OpenFDA":
            documents.append(doc.get("purpose", "") or doc.get("drug_name", ""))
        elif doc["source"] == "DrugBank":
            documents.append(doc.get("title", ""))

    rerank_results = co.rerank(
        query=query,
        documents=documents,
        top_n=top_n,
        model="rerank-english-v3.0"
    ).results

    return [raw_chunks[result.index] for result in rerank_results]

def generate_answer(query: str, context_docs: list, chat_history: list = None, tone: str = "friendly", use_rag: bool = True):
    context_texts = []
    for doc in context_docs:
        if doc["source"] == "MedlinePlus":
            context_texts.append(f"[MedlinePlus] {doc.get('title', '')}")
        elif doc["source"] == "OpenFDA":
            context_texts.append(f"[OpenFDA] {doc.get('purpose', '') or doc.get('drug_name', '')}")
        elif doc["source"] == "DrugBank":
            context_texts.append(f"[DrugBank] {doc.get('title', '')} — Description hidden due to license")

    context_text = "\n\n".join(context_texts) if use_rag else "No medical documents found. Please answer using general medical knowledge."

    chat_turns = ""
    if chat_history:
        for turn in chat_history[-6:]:
            role = turn["role"]
            content = turn["content"]
            chat_turns += f"{role.title()}: {content}\n"

    tone_instruction = {
        "friendly": "Use a warm and supportive tone, like a caring friend.",
        "professional": "Use a formal and clinical tone, like a medical practitioner.",
        "motivational": "Encourage the user with empowering and positive language."
    }.get(tone, "")

    prompt = f"""
You are a helpful, medically accurate assistant named MIIHA.
{tone_instruction}

Use the following:
- Provided chat history to maintain continuity.
- Medical context documents for factual responses.

Chat History:
{chat_turns}

Medical Context:
{context_text}

User: {query}
Assistant:"""

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=350,
        temperature=0.5,
        stop_sequences=["User:"]
    )

    return response.generations[0].text.strip()
