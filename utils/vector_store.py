import faiss
import numpy as np
def store_embeddings(embeddings):
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    vectors = np.array(embeddings).astype("float32")
    index.add(vectors)
    return index
def search_similar(index, query_embedding, top_k=5):
    query = np.array([query_embedding]).astype("float32")
    distances, indices = index.search(query, top_k)
    return indices[0]