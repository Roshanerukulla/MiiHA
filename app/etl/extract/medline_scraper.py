import requests
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from app.config.paths import (
    MEDLINE_XML_PATH,
    HEALTH_TOPICS_JSONL,
    MEDLINE_CHUNKS_PATH,
    MEDLINE_INDEX_PATH,
    MEDLINE_METADATA_PATH
)

# 1. Download XML if needed
def download_xml():
    url = "https://medlineplus.gov/xml/mplus_topics_2025-04-24.xml"
    if not MEDLINE_XML_PATH.exists() or MEDLINE_XML_PATH.stat().st_size == 0:
        response = requests.get(url)
        response.raise_for_status()
        MEDLINE_XML_PATH.parent.mkdir(parents=True, exist_ok=True)
        MEDLINE_XML_PATH.write_bytes(response.content)
        print("✅ Downloaded XML")
    else:
        print("📁 XML already exists")

# 2. Parse and filter English topics
def parse_xml():
    tree = ET.parse(MEDLINE_XML_PATH)
    root = tree.getroot()
    records = []
    for topic in root.findall(".//health-topic"):
        if topic.attrib.get("language", "English") != "English":
            continue
        records.append({
            "id": topic.attrib.get("id"),
            "title": topic.attrib.get("title"),
            "url": topic.attrib.get("url"),
            "language": topic.attrib.get("language", "English"),
            "date_created": topic.attrib.get("date-created"),
            "summary": topic.findtext("full-summary"),
            "also_called": [ac.text for ac in topic.findall("also-called")],
            "groups": [g.text for g in topic.findall("group")],
            "mesh_terms": [m.findtext("descriptor") for m in topic.findall("mesh-heading")],
            "see_references": [ref.text for ref in topic.findall("see-reference")],
            "primary_institute": topic.findtext("primary-institute"),
            "source_sites": [
                {
                    "title": site.attrib.get("title"),
                    "url": site.attrib.get("url"),
                    "category": site.findtext("information-category"),
                    "organization": site.findtext("organization")
                }
                for site in topic.findall("site")
            ]
        })
    HEALTH_TOPICS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_TOPICS_JSONL, "w", encoding="utf-8") as f:
        for rec in records:
            json.dump(rec, f, ensure_ascii=False)
            f.write("\n")
    print(f"✅ Parsed and saved {len(records)} records")
    return records

# 3. Clean and chunk summaries
def clean_html(text):
    return BeautifulSoup(text or "", "html.parser").get_text(separator="\n")

def chunk(text, max_words=150):
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def process_chunks(records):
    chunks = []
    for rec in records:
        cleaned = clean_html(rec.get("summary", ""))
        for i, part in enumerate(chunk(cleaned)):
            chunks.append({
                "id": f"{rec['id']}_{i}",
                "title": rec["title"],
                "url": rec["url"],
                "text": part,
                "source": "MedlinePlus"
            })
    MEDLINE_CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MEDLINE_CHUNKS_PATH, "w", encoding="utf-8") as f:
        for ch in chunks:
            json.dump(ch, f)
            f.write("\n")
    print(f"✅ Cleaned and chunked into {len(chunks)} entries")
    return chunks

# 4. Build FAISS index
def build_index(chunks):
    texts = [c["text"] for c in chunks]
    metadata = [{"id": c["id"], "title": c["title"], "url": c["url"]} for c in chunks]

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True)

    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype("float32"))

    MEDLINE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(MEDLINE_INDEX_PATH))

    MEDLINE_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MEDLINE_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("✅ FAISS index and metadata saved")

# Run everything
if __name__ == "__main__":
    download_xml()
    parsed = parse_xml()
    chunks = process_chunks(parsed)
    build_index(chunks)
