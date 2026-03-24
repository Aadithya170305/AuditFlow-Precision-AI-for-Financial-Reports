import os
import requests
from dotenv import load_dotenv
load_dotenv("../.env")
def create_embeddings(chunks):
    if not chunks:
        return []
    response = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "text-embedding-3-small",
            "input": chunks  
        }
    )
    result = response.json()
    if "data" in result:
        return [item["embedding"] for item in result["data"]]
    else:
        error_msg = result.get('error', {}).get('message', 'Unknown OpenAI Error')
        print(f"OpenAI Error: {error_msg}")
        raise Exception(f"Embedding failed: {error_msg}")