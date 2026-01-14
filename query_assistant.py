import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer, CrossEncoder

embedding_model = SentenceTransformer('all-mpnet-base-v2')
rerank_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

_cached_index = None
_cached_mapping = None
_cached_index_path = None
_cached_mapping_path = None

def expand_query(query):
    """Simple query expansion with corporate and financial synonyms."""
    synonyms = {
        "revenue": ["income", "turnover", "sales", "earnings"],
        "profit": ["bottom line", "net income", "pat", "ebitda"],
        "ceo": ["chief executive", "vijaykumar", "leader"],
        "chairperson": ["roshni", "nadar", "chairman"],
        "esg": ["sustainability", "environmental", "governance", "carbon"],
        "employees": ["workforce", "headcount", "staff", "talent"],
        "growth": ["increase", "expansion", "cagr"],
        "rsms": ["risk management", "safeguard"],
        "it": ["information technology", "software", "infrastructure"]
    }
    
    query_lower = query.lower()
    expanded_terms = []
    for term, syns in synonyms.items():
        if term in query_lower:
            expanded_terms.extend(syns)
            
    if expanded_terms:
        # Avoid making the query too messy, just add the most relevant ones
        return query + " " + " ".join(list(set(expanded_terms))[:3])
    return query

def retrieve_chunks(query, index_path, mapping_path, k=5, boost_keywords=None, section_filter=None):
    """Retrieves top-k relevant chunks with metadata filtering and re-ranking."""
    global _cached_index, _cached_mapping, _cached_index_path, _cached_mapping_path
    
    # Query Normalization & Expansion
    query = query.strip().replace("?", "").replace("!", "")
    
    # Clean potential PDF artifacts if pasted into query
    query = query.replace("/r_t.liga", "rt").replace("/r_f.liga", "rf")
    query = query.replace("t_t.liga", "tt").replace("f_f.liga", "ff")
    query = query.replace("/uni20B9", "₹")
    
    expanded_query = expand_query(query)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(index_path): index_path = os.path.join(base_dir, index_path)
    if not os.path.isabs(mapping_path): mapping_path = os.path.join(base_dir, mapping_path)
    
    if not os.path.exists(index_path) or not os.path.exists(mapping_path): return None
        
    if _cached_index_path != index_path:
        _cached_index = faiss.read_index(index_path)
        _cached_index_path = index_path
    
    if _cached_mapping_path != mapping_path:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            _cached_mapping = json.load(f)
        _cached_mapping_path = mapping_path
        
    index = _cached_index
    chunks = _cached_mapping
    import re
        
    query_vector = embedding_model.encode([expanded_query]).astype('float32')
    # Increase candidate pool for better recall
    distances, indices = index.search(query_vector, 100)
    
    candidates = []
    query_tokens = set(re.findall(r'\w{3,}', expanded_query.lower()))
    
    for i in range(100):
        idx = indices[0][i]
        if idx < len(chunks):
            chunk = chunks[idx].copy() # Work on a copy
            chunk_tokens = set(re.findall(r'\w{3,}', chunk['content'].lower()))
            overlap = len(query_tokens.intersection(chunk_tokens))
            
            # Hybrid pre-score: Inverse distance + lexical overlap boost
            semantic_score = 1.0 / (1.0 + distances[0][i])
            lexical_boost = overlap * 0.1
            chunk["pre_score"] = semantic_score + lexical_boost
            candidates.append(chunk)

    if not candidates:
        return []

    # Take top 50 for expensive re-ranking
    candidates.sort(key=lambda x: x.get("pre_score", 0), reverse=True)
    rerank_pool = candidates[:50]

    pairs = [[query, c['content']] for c in rerank_pool]
    rerank_scores = rerank_model.predict(pairs)
    
    # Prepare boosts from known entities
    entities = {} # Placeholder, will be passed from main_assistant in future or extracted
    
    for i, candidate in enumerate(rerank_pool):
        boost = 0
        if boost_keywords:
            content_lower = candidate['content'].lower()
            for kw in boost_keywords:
                if kw.lower() in content_lower: boost += 1.0 # Increased boost
        
        # Numerical exact match boost (Crucial for annual reports)
        query_numbers = re.findall(r'\b\d{2,}\b', query)
        content_text = candidate['content']
        for num in query_numbers:
            if num in content_text:
                boost += 2.0 # Significant boost for numbers
        
        # Section alignment boost
        if section_filter and section_filter.lower() in candidate.get('section', '').lower():
            boost += 1.5
            
        candidate["score"] = rerank_scores[i] + boost + 5.0 
        candidate["vector_distance"] = float(distances[0][i])

    rerank_pool.sort(key=lambda x: x['score'], reverse=True)
    results = rerank_pool[:k]
    
    return results

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
