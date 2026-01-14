import json
import os
import numpy as np
import faiss
import re
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

def get_bigrams(text):
    words = re.findall(r'\w{3,}', text.lower())
    return set(zip(words, words[1:]))

def retrieve_chunks(query, index_path, mapping_path, k=5, boost_keywords=None, section_filter=None):
    """Retrieves top-k relevant chunks with metadata filtering and re-ranking."""
    global _cached_index, _cached_mapping, _cached_index_path, _cached_mapping_path
    import re
    
    # Query Normalization & Expansion
    query_clean = query.strip().replace("?", "").replace("!", "")
    query_clean = query_clean.replace("/r_t.liga", "rt").replace("/r_f.liga", "rf")
    query_clean = query_clean.replace("t_t.liga", "tt").replace("f_f.liga", "ff")
    query_clean = query_clean.replace("/uni20B9", "₹")
    
    expanded_query = expand_query(query_clean)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(index_path): index_path = os.path.join(base_dir, index_path)
    if not os.path.isabs(mapping_path): mapping_path = os.path.join(base_dir, mapping_path)
    
    if not os.path.exists(index_path) or not os.path.exists(mapping_path): return None
        
    if _cached_index_path != index_path or _cached_index is None:
        _cached_index = faiss.read_index(index_path)
        _cached_index_path = index_path
    
    if _cached_mapping_path != mapping_path or _cached_mapping is None:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            _cached_mapping = json.load(f)
            # Pre-calculate bigrams for all chunks to speed up hybrid search
            for chunk in _cached_mapping:
                chunk['_bigrams'] = get_bigrams(chunk['content'])
        _cached_mapping_path = mapping_path
        
    index = _cached_index
    chunks = _cached_mapping
        
    # 1. Vector Search (Semantic)
    query_vector = embedding_model.encode([expanded_query]).astype('float32')
    distances, indices = index.search(query_vector, 120) 
    
    # 2. Hybrid RRF
    query_tokens = set(re.findall(r'\w{3,}', expanded_query.lower()))
    query_bigrams = get_bigrams(expanded_query)
    
    candidate_map = {}
    for rank, idx in enumerate(indices[0]):
        if idx < len(chunks):
            chunk = chunks[idx].copy()
            rrf_score = 1.0 / (60 + rank)
            
            content_lower = chunk['content'].lower()
            chunk_tokens = set(re.findall(r'\w{3,}', content_lower))
            overlap = len(query_tokens.intersection(chunk_tokens))
            
            # Use pre-calculated bigrams
            chunk_bigrams = chunk.get('_bigrams', set())
            bigram_overlap = len(query_bigrams.intersection(chunk_bigrams))
            
            lexical_score = (overlap * 0.05) + (bigram_overlap * 0.15)
            chunk["rrf_score"] = rrf_score + lexical_score
            candidate_map[idx] = chunk

    # Sort candidates by hybrid RRF score
    sorted_candidates = sorted(candidate_map.values(), key=lambda x: x["rrf_score"], reverse=True)
    rerank_pool = sorted_candidates[:45] # Balanced for speed/precision

    if not rerank_pool:
        return []

    # 3. Re-ranking (Cross-Encoder)
    pairs = [[query_clean, c['content']] for c in rerank_pool]
    rerank_scores = rerank_model.predict(pairs)
    
    for i, candidate in enumerate(rerank_pool):
        boost = 0
        if boost_keywords:
            content_lower = candidate['content'].lower()
            for kw in boost_keywords:
                if kw.lower() in content_lower: boost += 1.0 
        
        query_numbers = re.findall(r'\b\d{2,}\b', query_clean)
        content_text = candidate['content']
        for num in query_numbers:
            if num in content_text:
                boost += 2.0 
        
        if section_filter and section_filter.lower() in candidate.get('section', '').lower():
            boost += 1.5
            
        candidate["score"] = float(rerank_scores[i]) + boost + 6.0
        candidate["vector_distance"] = float(distances[0][i]) if i < len(distances[0]) else 100.0

    rerank_pool.sort(key=lambda x: x['score'], reverse=True)
    return rerank_pool[:k]

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
