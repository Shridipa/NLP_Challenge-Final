import json

import os

import numpy as np

import faiss

from sentence_transformers import SentenceTransformer

def create_index(chunks_path, index_output_path, mapping_output_path):

    print(f"Loading chunks from {chunks_path}...")

    with open(chunks_path, 'r', encoding='utf-8') as f:

        chunks = json.load(f)

    

    print("Initializing embedding model...")

    model = SentenceTransformer('all-mpnet-base-v2')

    

    texts = [chunk['content'] for chunk in chunks]

    

    print(f"Generating embeddings for {len(texts)} chunks...")

    embeddings = model.encode(texts, show_progress_bar=True)

    embeddings = np.array(embeddings).astype('float32')

    

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)

    

    print("Adding embeddings to index...")

    index.add(embeddings)

    

    print(f"Saving index to {index_output_path}...")

    faiss.write_index(index, index_output_path)

    

    with open(mapping_output_path, 'w', encoding='utf-8') as f:

        json.dump(chunks, f, indent=2)

    

    print("Indexing complete.")

def search_index(query, index_path, mapping_path, k=5):

    print(f"Searching for: '{query}'")

    model = SentenceTransformer('all-mpnet-base-v2')

    index = faiss.read_index(index_path)

    

    with open(mapping_path, 'r', encoding='utf-8') as f:

        chunks = json.load(f)

    

    query_vector = model.encode([query]).astype('float32')

    distances, indices = index.search(query_vector, k)

    

    results = []

    for i in range(k):

        idx = indices[0][i]

        if idx < len(chunks):

            results.append({

                "score": float(distances[0][i]),

                "metadata": chunks[idx]

            })

            

    return results

if __name__ == "__main__":

    chunks_file = "chunks.json"

    index_file = "faq_index.faiss"

    mapping_file = "chunks_mapping.json"

    

    if os.path.exists(chunks_file):

        create_index(chunks_file, index_file, mapping_file)

        

        print("\n--- Smoke Test ---")

        test_query = "revenue growth"

        search_results = search_index(test_query, index_file, mapping_file, k=3)

        

        for i, res in enumerate(search_results):

            meta = res['metadata']

            print(f"Result {i+1} (Score: {res['score']:.4f}):")

            print(f"  Page: {meta['page_number']}")

            print(f"  Snippet: {meta['content'][:150]}...")

            print("-" * 20)

    else:

        print(f"Error: {chunks_file} not found.")

