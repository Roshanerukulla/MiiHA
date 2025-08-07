# app/services/query_service.py

import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import cohere

from app.config.paths import (
    MEDLINE_INDEX_PATH,
    OPENFDA_INDEX_PATH,
    MEDLINE_METADATA_PATH,
    OPENFDA_METADATA_PATH,
    DRUGBANK_INDEX_PATH,
    DRUGBANK_METADATA_PATH
)
from app.services.firestore_user_service import get_user_profile

# Load environment and API keys
load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Load FAISS indexes and metadata
medline_index = faiss.read_index(str(MEDLINE_INDEX_PATH))
openfda_index = faiss.read_index(str(OPENFDA_INDEX_PATH))
drugbank_index = None

with open(MEDLINE_METADATA_PATH, "r", encoding="utf-8") as f:
    medline_metadata = json.load(f)
with open(OPENFDA_METADATA_PATH, "r", encoding="utf-8") as f:
    openfda_metadata = json.load(f)
try:
    drugbank_index = faiss.read_index(str(DRUGBANK_INDEX_PATH))
    with open(DRUGBANK_METADATA_PATH, "r", encoding="utf-8") as f:
        drugbank_metadata = json.load(f)
except Exception as e:
    print("⚠️ DrugBank index or metadata not loaded:", e)
    drugbank_metadata = []

# Heuristics

def simulate_rag_chunk_quality(chunks):
    return 0.6 if len(chunks) >= 2 else 0.2

def is_general_prompt(prompt: str) -> bool:
    general_keywords = ["hello", "hi", "thanks", "goodbye", "hey", "sup", "yo", "what's up"]
    return (
        any(k in prompt for k in general_keywords)
        and len(prompt.split()) <= 5
        and not any(k in prompt for k in ["medicine", "source", "dose", "treatment", "symptom", "prescription"])
    )

def is_health_query(prompt: str) -> bool:
    keywords = [
        "disease", "medicine", "drug", "dose", "symptom", "treatment", "side effect",
        "diagnosis", "condition", "health", "prescription", "nausea", "dizziness",
        "mental", "depression", "anxiety", "therapy", "counseling", "panic", "emotional", "mood",
        "infection", "pain", "vomiting", "blood", "pressure", "heart", "fatigue", "urine"
    ]
    return any(k in prompt.lower() for k in keywords)

def is_follow_up(prompt: str, chat_history: list) -> bool:
    if not chat_history:
        return False
    follow_up_phrases = ["continue", "what about", "also", "you said", "remember", "previous", "earlier", "next", "what else"]
    return any(p in prompt.lower() for p in follow_up_phrases)

def is_mixed_topic(prompt: str) -> bool:
    political_keywords = ["trump", "biden", "president", "election"]
    health_keywords = ["medicine", "dose", "treatment", "diabetes"]
    return any(pk in prompt.lower() for pk in political_keywords) and any(hk in prompt.lower() for hk in health_keywords)

# Main Query Handler

async def query_rag(query: str, user_id: str, chat_history: list = None, top_k: int = 15, tone: str = "friendly"):
    chat_history = chat_history or []
    lower_query = query.strip().lower()

    user_profile = await get_user_profile(user_id)
    preferred_name = user_profile.get("preferred_name", "there") if user_profile else "there"

    if is_mixed_topic(lower_query):
        return {
            "query": query,
            "answer": f"{preferred_name.title()}, this looks like a mix of health and political topics. I can help you with medical or health questions—could you clarify what you'd like to focus on?",
            "sources": []
        }

    if any(p in lower_query for p in ["source", "where did you get", "how accurate", "based on what"]):
        answer = generate_answer(query, [], chat_history, tone, use_rag=False, preferred_name=preferred_name)
        return {"query": query, "answer": answer, "sources": []}

    is_general = is_general_prompt(lower_query)
    is_follow_up_flag = is_follow_up(lower_query, chat_history)
    is_health = is_health_query(lower_query)

    if not (is_health or is_follow_up_flag):
        answer = generate_answer(query, [], chat_history, tone, use_rag=False, preferred_name=preferred_name)
        return {"query": query, "answer": answer, "sources": []}

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
            if len(chunk.get("purpose", "")) > 20:
                combined_chunks.append(chunk)

    if drugbank_index:
        try:
            db_scores, db_indices = drugbank_index.search(np.array([query_vector]), top_k)
            for i in db_indices[0]:
                if 0 <= i < len(drugbank_metadata):
                    chunk = dict(drugbank_metadata[i])
                    chunk["source"] = "DrugBank"
                    if len(chunk.get("title", "")) > 5:
                        combined_chunks.append(chunk)
        except Exception as e:
            print(" DrugBank query failed:", e)

    combined_chunks = [doc for doc in combined_chunks if doc.get("title") or doc.get("purpose") or doc.get("drug_name")]

    reranked_chunks = rerank_with_cohere(query, combined_chunks, top_n=3)
    use_rag = simulate_rag_chunk_quality(reranked_chunks) > 0.4
    answer = generate_answer(query, reranked_chunks if use_rag else [], chat_history, tone, use_rag, preferred_name)

    safe_sources = []
    if use_rag:
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
        "sources": safe_sources
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


def generate_answer(query: str, context_docs: list, chat_history: list = None, tone: str = "friendly", use_rag: bool = True, preferred_name: str = "there"):
    chat_history = chat_history or []
    lower_query = query.strip().lower()

    # ✅ Only greet once at the start of the conversation
    if len(chat_history) <= 1 and is_general_prompt(lower_query):
        return f"Hello {preferred_name.title()}! How can I assist you today?"

    if any(p in lower_query for p in ["do you remember", "what we spoke", "context", "previous chat", "earlier you said"]):
        if chat_history and len(chat_history) >= 2:
            last_topic = chat_history[-2]["content"]
            return f"You were previously asking about: \"{last_topic}\". Would you like to continue on that topic, {preferred_name}?"
        else:
            return f"I'm here to help, {preferred_name}. Could you remind me what you were referring to?"

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
        for turn in chat_history[-8:]:
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
Greet the user as {preferred_name.title()} in the first message. In follow-up responses, use the name naturally if relevant, but avoid repeating the greeting.



{tone_instruction}

Use the following:
- Provided chat history to maintain continuity.
- Medical context documents for factual responses.

Chat History:
{chat_turns}

Medical Context:
{context_text}

User ({preferred_name}): {query}
Assistant:"""

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=350,
        temperature=0.5,
        stop_sequences=["User:"]
    )

    return response.generations[0].text.strip()
