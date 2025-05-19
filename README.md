# MIIHA — Multimodal Intelligent Health Assistant

MIIHA is a secure, intelligent health assistant that answers user questions using Retrieval-Augmented Generation (RAG) over trusted medical sources like MedlinePlus and OpenFDA. It supports JWT-based authentication, onboarding, and context-aware LLM responses with source transparency. MongoDB integration is included for session tracking.

---

## Features

- User registration, login, and JWT-based authentication
- Onboarding: profile, medications, and preference setup
- RAG-powered Q&A with MiniLM + FAISS + Cohere LLM
- Data sourced from MedlinePlus and OpenFDA (via ETL)
- Smart fallback generation if retrieval is weak
- MongoDB integration for chat history and user data
- Modular FastAPI backend using Uvicorn

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/miiha.git
cd miiha

#set up
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

#installations 
pip install uv
uv pip install -r requirements.txt

#set up .env file 
COHERE_API_KEY=your-cohere-api-key
DATABASE_NAME=miiha_db
MONGODB_URI=mongodb://localhost:27017

#running the app
uvicorn app.main:app --reload

#Once running, open your browser at:
http://localhost:8000/docs

app/
├── api/                 # FastAPI endpoints
├── core/                # JWT logic, auth dependencies
├── services/            # Auth, onboarding, RAG query logic
├── config/              # App constants, paths, LLM configs
├── db/                  # MongoDB and FAISS index loaders
│   ├── mongodb.py
│   └── *.index
├── data/
│   ├── raw/             # Original MedlinePlus/XML, OpenFDA JSON
│   ├── processed/       # Cleaned, chunked, ready-for-embedding
│   ├── metadata/        # Metadata to map FAISS vector IDs to sources
├── etl/
│   ├── extract/         # medline_scraper.ipynb, openfda_api.ipynb
│   ├── transform/       # cleaner.ipynb
├── rag/                 # Embedding, reranking, prompt engineering
├── main.py              # FastAPI app instance


#steps
RAG Query Flow
User sends a health question to /api/v1/query/full

Query is embedded using MiniLM

FAISS searches MedlinePlus and OpenFDA indexes

Results are reranked using Cohere Rerank API

Final answer is generated using Cohere LLM with fallback

Sources are returned along with the answer

How to Rebuild Indexes
MedlinePlus:

Use etl/extract/medline_scraper.ipynb to generate topics

Use rag/faiss_index.ipynb to embed and build miiha_medline.index

OpenFDA:

Use etl/extract/openfda_api.ipynb to pull and clean drug labels

Use rag/openfda_index.ipynb to embed and build openfda_all_drugs.index