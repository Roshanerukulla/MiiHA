from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# App directories
APP_DIR = BASE_DIR / "app"
DATA_DIR = APP_DIR / "data"
DB_DIR = APP_DIR / "db"
ETL_DIR = APP_DIR / "etl"
RAG_DIR = APP_DIR / "rag"

# Data directories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
METADATA_DIR = DATA_DIR / "metadata"

# Example file paths (optional shortcuts)
MEDLINE_CHUNKS_PATH = PROCESSED_DATA_DIR / "chunks_medline.jsonl"
MEDLINE_XML_PATH = RAW_DATA_DIR / "medlineplus_healthtopics.xml"
HEALTH_TOPICS_JSONL = PROCESSED_DATA_DIR / "medlineplus_health_topics.jsonl"

OPENFDA_RAW_PATH = RAW_DATA_DIR / "openfda_all_drugs.json"
MEDLINE_METADATA_PATH = METADATA_DIR / "medline_metadata.json"
OPENFDA_METADATA_PATH = METADATA_DIR / "openfda_all_drugs_metadata.json"

# FAISS index paths
MEDLINE_INDEX_PATH = DB_DIR / "miiha_medline.index"
OPENFDA_INDEX_PATH = DB_DIR / "openfda_all_drugs.index"

DRUGBANK_XML_PATH = RAW_DATA_DIR / "drugbank_full_database.xml"
DRUGBANK_CHUNKS_PATH = PROCESSED_DATA_DIR / "chunks_drugbank.jsonl"
DRUGBANK_INDEX_PATH = DB_DIR / "drugbank.index"
DRUGBANK_METADATA_PATH = METADATA_DIR / "drugbank_metadata.json"
