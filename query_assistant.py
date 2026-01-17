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

                                                                     

    synonyms = {

        "revenue": ["income", "turnover", "sales", "earnings", "top line"],

        "profit": ["bottom line", "net income", "pat", "ebitda", "ebit"],

        "ceo": ["chief executive", "vijaykumar", "leader", "managing director"],

        "chairperson": ["roshni", "nadar", "chairman", "lead"],

        "esg": ["sustainability", "environmental", "governance", "carbon", "brsr"],

        "employees": ["workforce", "headcount", "staff", "talent", "attrition", "retention"],

        "growth": ["increase", "expansion", "cagr", "year-on-year", "yoy"],

        "rsms": ["risk management", "safeguard", "mitigation"],

        "rsus": ["stock units", "equity", "vesting", "lti", "share-based payment"],

        "it": ["information technology", "software", "infrastructure", "digital"],

        "chart": ["graphic", "visualization", "image", "diagram", "figure"],

        "graph": ["chart", "plot", "trend", "data visualization"],

        "dividend": ["payout", "shareholder return", "quarterly dividend", "tsr"],

        "audit": ["statutory", "auditor", "compliance", "report"]

    }

    

    query_lower = query.lower()

    expanded_terms = []

                                                                  

    if "vijaykumar" in query_lower: expanded_terms.append("CEO")

    if "roshni" in query_lower or "nadar" in query_lower: expanded_terms.append("Chairperson")

    

    for term, syns in synonyms.items():

        if term in query_lower:

            expanded_terms.extend(syns)

            

    if expanded_terms:

                                                                           

        return query + " " + " ".join(list(set(expanded_terms))[:4])

    return query

def get_bigrams(text):

    words = re.findall(r'\w{3,}', text.lower())

                                                                    

    stops = {'the', 'and', 'for', 'with', 'from', 'that', 'this'}

    words = [w for w in words if w not in stops]

    return set(zip(words, words[1:]))

def retrieve_chunks(query, index_path, mapping_path, k=5, boost_keywords=None, section_filter=None):

                                                                                 

    global _cached_index, _cached_mapping, _cached_index_path, _cached_mapping_path

    

                                     

    query_clean = query.strip().replace("?", "").replace("!", "")

                                                                

    

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

                                                       

            for chunk in _cached_mapping:

                if 'bigrams' not in chunk:

                    chunk['bigrams'] = list(get_bigrams(chunk['content']))

        _cached_mapping_path = mapping_path

    

    index = _cached_index

    chunks = _cached_mapping

        

                                            

                                                        

    query_vector = embedding_model.encode([expanded_query]).astype('float32')

    distances_sem, indices_sem = index.search(query_vector, 1000) 

    

                                          

    stops = {'what', 'which', 'who', 'the', 'and', 'for', 'with', 'from', 'that', 'this', 'date', 'name', 'how', 'when', 'where', 'why', 'does', 'did', 'has', 'have', 'been', 'were', 'was', 'is', 'are', 'it', 'in', 'on', 'at', 'about'}

    query_tokens = set(re.findall(r'\w{3,}', query_clean.lower()))

    query_tokens = {t for t in query_tokens if t not in stops}

    

    candidate_map = {}

    for rank, idx in enumerate(indices_sem[0]):

        if idx < len(chunks):

            chunk = chunks[idx].copy()

            content_lower = chunk['content'].lower()

            chunk_tokens = set(re.findall(r'\w{3,}', content_lower))

            

                                 

            overlap = len(query_tokens.intersection(chunk_tokens))

            

                            

            query_bigrams = get_bigrams(query_clean)

            chunk_bigrams = set(chunk.get('bigrams', []))

            bigram_overlap = len(query_bigrams.intersection(chunk_bigrams))

            

                                                          

            rrf_base = 1.0 / (60 + rank)

            lex_score = (overlap * 0.5) + (bigram_overlap * 1.0)                    

            

            chunk["rrf_score"] = rrf_base + lex_score

            candidate_map[idx] = chunk

                                                                          

    sorted_candidates = sorted(candidate_map.values(), key=lambda x: x["rrf_score"], reverse=True)

    rerank_pool = sorted_candidates[:300]

    if not rerank_pool: return []

                                                                   

    pairs = [[query_clean, c['content']] for c in rerank_pool]

    rerank_scores = rerank_model.predict(pairs)

    

    for i, candidate in enumerate(rerank_pool):

        boost = 0.0

        content_lower = candidate['content'].lower()

        

                                          

        important_names = ["vijaykumar", "roshni", "nadar", "hcltech", "hcl software", "hcl", "vijayakumar", "shiv", "walia", "inspeq", "ethisphere", "forbes", "newsweek", "microsoft", "google", "dell", "intel", "subsidiary", "india", "incorporated", "financial", "asset", "capital"]

        for name in important_names:

            if name in query_clean.lower() and name in content_lower:

                boost += 12.0                                   

        

                                             

        query_numbers = re.findall(r'\b\d{2,}\b', query_clean)

        for num in query_numbers:

            if num in candidate['content']:

                boost += 10.0                         

        

                                                                        

        if any(kw in query_clean.lower() for kw in ["revenue", "profit", "report", "rsus", "payment", "date", "incorporate", "company", "what is"]):

            boilerplate_kws = ["forward-looking", "terms of use", "table of contents", "index", "notice of", "cautionary", "disclaimer"]

            if any(bk in content_lower for bk in boilerplate_kws):

                boost -= 10.0

            

                                                                                   

            if len(candidate['content'].split()) < 40:

                boost -= 5.0

            

        candidate["score"] = float(rerank_scores[i]) + boost

        

                                                                              

        if query_clean.lower() in content_lower:

            candidate["score"] += 25.0

        candidate["vector_distance"] = float(distances_sem[0][i]) if i < len(distances_sem[0]) else 100.0

    rerank_pool.sort(key=lambda x: x['score'], reverse=True)

    return rerank_pool[:k]

def format_rag_prompt(user_query, retrieved_chunks):

                                 

    system_msg = (

                                                                                                

                           

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

