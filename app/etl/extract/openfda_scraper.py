import requests
import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from app.config.paths import (
    OPENFDA_RAW_PATH,
    OPENFDA_METADATA_PATH,
    OPENFDA_INDEX_PATH,
    PROCESSED_DATA_DIR
)

# 1. Download OpenFDA drug labels
def download_openfda():
    url = "https://api.fda.gov/drug/label.json"
    params = {"limit": 1000}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    OPENFDA_RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OPENFDA_RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Saved raw OpenFDA data: {len(data.get('results', []))} records")
    return data

# 2. Parse drug labels
def parse_fda_data(raw_data):
    processed = []
    for item in raw_data.get("results", []):
        usage = item.get("indications_and_usage", [""])[0] if "indications_and_usage" in item else ""
        warnings = item.get("warnings", [""])[0] if "warnings" in item else ""
        description = (usage + "\n" + warnings).strip()
        if not description:
            continue

        processed.append({
            "id": item.get("id", ""),
            "brand_name": item.get("openfda", {}).get("brand_name", ["Unknown"])[0],
            "generic_name": item.get("openfda", {}).get("generic_name", ["Unknown"])[0],
            "route": item.get("openfda", {}).get("route", ["Unknown"])[0],
            "purpose": item.get("purpose", [""])[0] if "purpose" in item else "",
            "description": description,
            "source": "OpenFDA"
        })

    output_path = PROCESSED_DATA_DIR / "openfda_all_drugs.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in processed:
            json.dump(record, f)
            f.write("\n")

    print(f"✅ Saved processed OpenFDA data: {len(processed)} records")
    return processed

# 3. Build FAISS index
def build_index(docs):
    texts = [doc["description"] for doc in docs]
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype("float32"))

    OPENFDA_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(OPENFDA_INDEX_PATH))

    metadata = [{
        "id": doc["id"],
        "brand_name": doc["brand_name"],
        "generic_name": doc["generic_name"],
        "purpose": doc["purpose"],
        "route": doc["route"],
        "source": "OpenFDA"
    } for doc in docs]

    OPENFDA_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OPENFDA_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ FAISS index and metadata saved: {len(metadata)} entries")

# Run all steps
if __name__ == "__main__":
    raw = download_openfda()
    processed = parse_fda_data(raw)
    build_index(processed)
