import os

COHERE_RERANK_MODEL: str = os.getenv("COHERE_RERANK_MODEL", "rerank-english-v3.0")
COHERE_GENERATE_MODEL: str = os.getenv("COHERE_GENERATE_MODEL", "command-r-plus")
SENTENCE_TRANSFORMER_MODEL: str = os.getenv("ST_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "300"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.5"))
TOP_K_DEFAULT: int = int(os.getenv("TOP_K_DEFAULT", "15"))
RERANK_TOP_N: int = int(os.getenv("RERANK_TOP_N", "3"))
