import xml.etree.ElementTree as ET
import json
from bs4 import BeautifulSoup
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from app.config.paths import (
    DRUGBANK_XML_PATH,
    DRUGBANK_CHUNKS_PATH,
    DRUGBANK_INDEX_PATH,
    DRUGBANK_METADATA_PATH
)

def clean_html(text):
    return BeautifulSoup(text or "", "html.parser").get_text(separator="\n")

def chunk(text, max_words=150):
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def parse_drugbank_xml():
    tree = ET.parse(DRUGBANK_XML_PATH)
    root = tree.getroot()
    ns = {'db': 'http://www.drugbank.ca'}

    drugs = []
    for drug in root.findall("db:drug", ns):
        name = drug.findtext("db:name", default="", namespaces=ns)
        desc = drug.findtext("db:description", default="", namespaces=ns)
        url = f"https://go.drugbank.com/drugs/{drug.findtext('db:drugbank-id', namespaces=ns)}"
        cleaned = clean_html(desc)
        chunks = chunk(cleaned)

        for i, part in enumerate(chunks):
            drugs.append({
                "id": f"{drug.findtext('db:drugbank-id', namespaces=ns)}_{i}",
                "title": name,
                "url": url,
                "text": part,
                "source": "DrugBank"
            })

    with open(DRUGBANK_CHUNKS_PATH, "w", encoding="utf-8") as f:
        for ch in drugs:
            json.dump(ch, f)
            f.write("\n")

    return drugs

def build_faiss_index(chunks):
    texts = [c["text"] for c in chunks]
    metadata = [{"id": c["id"], "title": c["title"], "url": c["url"]} for c in chunks]

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True)

    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(np.array(embeddings).astype("float32"))

    faiss.write_index(index, str(DRUGBANK_INDEX_PATH))
    with open(DRUGBANK_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    chunks = parse_drugbank_xml()
    build_faiss_index(chunks)
    print(f"✅ Processed {len(chunks)} DrugBank chunks")
