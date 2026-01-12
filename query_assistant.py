import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

print("Loading global SentenceTransformer model (all-MiniLM-L6-v2)...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve_chunks(query, index_path, mapping_path, k=5, boost_keywords=None):
    """Retrieves top-k relevant chunks and optionally re-ranks based on keywords."""
    
    # Resolve absolute paths relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # If paths are just filenames, prepend base_dir
    if not os.path.isabs(index_path):
        index_path = os.path.join(base_dir, index_path)
    if not os.path.isabs(mapping_path):
        mapping_path = os.path.join(base_dir, mapping_path)
        
    if not os.path.exists(index_path) or not os.path.exists(mapping_path):
        print(f"[ERROR] Index/Mapping file not found at: {index_path}, {mapping_path}")
        return None
        
    index = faiss.read_index(index_path)
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    query_vector = embedding_model.encode([query]).astype('float32')
    distances, indices = index.search(query_vector, k*2) # Fetch more for re-ranking
    
    results = []
    for i in range(k*2):
        idx = indices[0][i]
        score = float(distances[0][i])
        
        if idx < len(chunks):
            chunk_data = chunks[idx].copy()
            content_lower = chunk_data['content'].lower()
            
            # Re-ranking logic
            if boost_keywords:
                for kw in boost_keywords:
                    if kw.lower() in content_lower:
                        score -= 0.15 # Strong boost (lower distance)
            
            chunk_data["score"] = score
            results.append(chunk_data)

    # Sort by new scores and take top k
    results.sort(key=lambda x: x['score'])
    results = results[:k]
    
    # Filter by final threshold
    filtered_results = [r for r in results if r['score'] < 1.30] 
    
    return filtered_results

def format_rag_prompt(user_query, retrieved_chunks):
    """Formats the RAG prompt."""
    system_msg = (
        "System: Follow global rules. Use ONLY the Annual Report for finance/strategy answers. "
        "Cite exact pages."
    )
    
    chunks_str = ""
    for chunk in retrieved_chunks:
        chunks_str += f"- [Page {chunk['page_number']} | Section: {chunk.get('section', 'N/A')}]\n"
        chunks_str += f"  {chunk['content']}\n"
        
    prompt = f"""{system_msg}

User Query: {user_query}

Retrieved Chunks (Top-k):
{chunks_str}

Instruction:
- Answer ONLY using the retrieved chunks.
- Include citations like [Annual Report 2024–25, Page {{page_number}}] after each claim.
- If the answer cannot be grounded, say: "I could not find this information in the dataset."
- Keep the answer concise and precise; preserve numeric values.
"""
    return prompt

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "What was HCLTech's revenue growth in FY25?"
    index_file = "faq_index.faiss"
    mapping_file = "chunks_mapping.json"
    
    chunks = retrieve_chunks(query, index_file, mapping_file)
    if chunks:
        rag_prompt = format_rag_prompt(query, chunks)
        print(rag_prompt)
    else:
        print("Error: Index or mapping not found.")
