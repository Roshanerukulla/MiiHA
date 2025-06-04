import cohere
import os
from dotenv import load_dotenv

load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))

models_to_test = [
    "rerank-english-v3.0",
    "rerank-english-v2.0",
    "embed-english-v3.0",
    "command-r",
    "command-r-plus"
]

for model_name in models_to_test:
    try:
        if "rerank" in model_name:
            result = co.rerank(
                query="What is diabetes?",
                documents=["Doc 1", "Doc 2", "Doc 3"],
                top_n=2,
                model=model_name
            )
        else:
            result = co.generate(
                model=model_name,
                prompt="Explain type 2 diabetes in simple terms.",
                max_tokens=50
            )

        print(f"✅ Model '{model_name}' is available and works.")
    except Exception as e:
        print(f"❌ Model '{model_name}' failed. Error: {e}")
