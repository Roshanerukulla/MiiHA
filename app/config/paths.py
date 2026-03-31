import os
from pathlib import Path

# Project root: three levels up from this file (app/config/paths.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

FAISS_DIR = Path(os.getenv("FAISS_DIR", str(BASE_DIR / "app" / "db")))
METADATA_DIR = Path(os.getenv("METADATA_DIR", str(BASE_DIR / "app" / "data" / "metadata")))

MEDLINE_INDEX_PATH = FAISS_DIR / "miiha_medline.index"
OPENFDA_INDEX_PATH = FAISS_DIR / "openfda_all_drugs.index"
MEDLINE_METADATA_PATH = METADATA_DIR / "medline_metadata.json"
OPENFDA_METADATA_PATH = METADATA_DIR / "openfda_all_drugs_metadata.json"
