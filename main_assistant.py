import json

import sys

import os

import re

from transformers import pipeline

from intent_detector import detect_intent

from ner_extractor import extract_entities

from sentiment_analyzer import analyze_sentiment_and_urgency

from query_assistant import retrieve_chunks

from agent_policy import decide_next_step

from action_generator import generate_action_json

from clarifier import generate_clarification

from citation_enforcer import verify_and_enforce_citations

from ui_formatter import format_ui_response

generator = pipeline("text2text-generation", model="google/flan-t5-small")

def synthesize_answer(query, chunks):

    if isinstance(query, list): query = " ".join([str(x) for x in query])
    if not isinstance(query, str): query = str(query)
    if not query or not query.strip():
        return "I'm sorry, I didn't catch that. Could you please rephrase your request?"
                                                                                        

    if not chunks:

        return "I could not find this information in the dataset."

        

                                         

                                                                                                    

                                                                 

    top_references = []

    all_pages = set()

    for i, c in enumerate(chunks[:3]):

        top_references.append(f"[REF PAGE {c['page_number']}]:\n{c['content']}")

        all_pages.add(c['page_number'])

    

                                                                                    

    for c in chunks[:10]:

        all_pages.add(c['page_number'])

    

    sorted_pages = sorted(list(all_pages))

    sources_str = " | ".join([f"Page {p}" for p in sorted_pages])

    

                                     

    context = "\n\n".join([f"Page {c['page_number']}: {c['content']}" for c in chunks[:5]])

    

    prompt = (
        f"Context: {context}\n\n"
        f"Question: {query}\n\n"
        f"Instruction: Provide a highly detailed answer using the context. Include all figures and specific names.\n\n"
        f"Answer:"
    )
    
    result = generator(prompt, max_new_tokens=200, do_sample=False, truncation=True)

    synthesized = result[0]['generated_text'].strip()

    

    ref_block = "\n\n".join(top_references)

    

    return (
        f"{synthesized}\n\n"
        f"--- DETAILED DATA REFERENCES ---\n{ref_block}\n\n"
        f"[Annual Report 2024–25 Sources: {sources_str}]"
    )

def run_pipeline(user_query, history=None):

                                              

    if isinstance(user_query, dict):

        user_query = user_query.get("text", "")

    

    if isinstance(user_query, dict): user_query = user_query.get("text", "")
    if isinstance(user_query, list): user_query = " ".join([str(x) for x in user_query])
    if not isinstance(user_query, str): user_query = str(user_query)

    if not user_query or not user_query.strip():

        return "I'm sorry, I didn't catch that. Could you please rephrase your request?"

    print(f"\n--- PROCESSING QUERY: {user_query} ---\n")

    

    intent_data = detect_intent(user_query)

    intent = intent_data["intent"]

    

    previous_action_intent = None

    historical_entities = {}

    conversation_context = []

    

    if history:

                                                                     

        for msg in reversed(history[-5:]):

            if isinstance(msg, dict):

                m = msg

            elif isinstance(msg, (list, tuple)):

                m = {"role": "user", "content": msg[0]} if len(msg) > 0 else {}

            else:

                m = msg.__dict__

            

            if m.get("role") == "user":

                user_msg = m["content"]

                if isinstance(user_msg, list):

                    user_msg = " ".join([item["text"] for item in user_msg if item.get("type") == "text"])

                

                if not user_msg: continue

                conversation_context.insert(0, user_msg)

                prev_intent_data = detect_intent(user_msg)

                if prev_intent_data["intent"].startswith("action_") and not previous_action_intent:

                    previous_action_intent = prev_intent_data["intent"]

                

                prev_entities = extract_entities(user_msg)

                for k, v in prev_entities.items():

                    if v and v != "..." and v not in ["Low|Medium|High", "TBD"]:

                        if k not in historical_entities or historical_entities[k] in ["...", "TBD", "Low|Medium|High"]:

                            historical_entities[k] = v

            

    current_entities = extract_entities(user_query)

    entities = current_entities.copy()

    

    informational_keywords = ["who is", "tell me about", "what is", "where is", "how many", "revenue", "about", "goals", "policy", "sustainability", "esg", "cfo", "headcount", "strategy", "growth", "profit", "margin", "ebitda", "dividend"]

    is_informational_query = any(k in user_query.lower() for k in informational_keywords)

    

    is_simple_info_response = False

    query_words = user_query.strip().split()

    if len(query_words) <= 5 and not is_informational_query:

        has_simple_value = any(current_entities.get(key, "...") != "..." for key in ["date", "priority", "department", "employee_id", "application_name"])

        if has_simple_value and intent == "other":

            is_simple_info_response = True

    should_adopt_previous = False

                                                                         

    is_continuation_like = any(k in user_query.lower() for k in ["more", "detail", "elaborate", "tell me more", "go on", "what about", "and then", "yes", "confirm", "ok", "go ahead", "yep", "sure"])

    

    if (previous_action_intent or (history and len(history) > 0)) and intent == "other" and not is_informational_query:

                                                                

        prev_intent = previous_action_intent

        if not prev_intent and history:

                                                   

            last_user_msg = history[-2]["content"] if len(history) >= 2 else ""

            if last_user_msg:

                prev_intent = detect_intent(last_user_msg)["intent"]

        if prev_intent and (prev_intent.startswith("action_") or prev_intent.startswith("ask_")):

            continuation_keywords = ["already", "provided", "mentioned", "said", "told you", "gave you"]

            has_continuation_kws = any(k in user_query.lower() for k in continuation_keywords)

            

            if is_simple_info_response or has_continuation_kws or is_continuation_like or intent_data["confidence"] < 0.4:

                should_adopt_previous = True

                intent = prev_intent

                intent_data["intent"] = intent

                intent_data["confidence"] = 0.85

    entities = current_entities.copy()

    global_entities = ["employee_id", "department"] 

    

    if should_adopt_previous or (intent.startswith("action_") and previous_action_intent == intent):

        for k, v_hist in historical_entities.items():

            v_curr = entities.get(k, "...")

            if (not v_curr or v_curr in ["...", "TBD"]) and v_hist and v_hist not in ["...", "TBD"]:

                entities[k] = v_hist

    else:

        for k in global_entities:

            v_hist = historical_entities.get(k)

            v_curr = entities.get(k, "...")

            if (not v_curr or v_curr in ["...", "TBD"]) and v_hist:

                 entities[k] = v_hist

    

    sentiment_data = analyze_sentiment_and_urgency(user_query)

    

    retrieval_score = 0.0

    retrieved_chunks = []

    rag_answer = ""

    

    is_policy_query = any(k in user_query.lower() for k in ["policy", "guideline", "rules", "terms", "entitlement", "duration", "leave", "holiday"])

    boost_kws = []

    if is_policy_query:

        boost_kws = ["policy", "eligibility", "weeks", "months", "benefit", "guidelines", "entitlement", "leave", "holiday"]

    elif any(k in user_query.lower() for k in ["cfo", "leadership", "ceo", "chairman", "shiv", "roshni"]):

        boost_kws = ["chief", "officer", "director", "leadership", "management", "founder", "chairman", "secretary"]

    elif any(k in user_query.lower() for k in ["revenue", "growth", "profit", "financial", "results"]):

        boost_kws = ["revenue", "profit", "growth", "financial", "margin", "ebitda", "consolidated", "income"]

    if intent.startswith("ask_") or is_informational_query:

        if not intent.startswith("ask_"):

            hr_kws = ["policy", "leave", "holiday", "benefit", "payroll", "salary", "pf", "insurance", "hr", "recruitment", "headcount"]

            if any(k in user_query.lower() for k in hr_kws):

                intent = "ask_hr"

            elif any(k in user_query.lower() for k in ["ceo", "cfo", "chairman", "roshni", "shiv", "vijaykumar", "leader", "leadership", "board", "director"]):

                intent = "ask_people"

            else:

                intent = "ask_finance" 

            intent_data["intent"] = intent 

            intent_data["confidence"] = 0.8

        section_map = {

            "ask_finance": "Financial",

            "ask_hr": "Human",

            "ask_people": "Governance",

            "ask_it_policy": "IT"

        }

        target_section = section_map.get(intent)

        if intent == "ask_people":

            boost_kws = ["ceo", "cfo", "chairman", "chairperson", "leader", "executive", "founder", "director", "board", "management", "biography", "profile"]

        

        base_dir = os.path.dirname(os.path.abspath(__file__))

        index_file = os.path.join(base_dir, "faq_index.faiss")

        mapping_file = os.path.join(base_dir, "chunks_mapping.json")

        

        if not os.path.exists(index_file) or not os.path.exists(mapping_file):

            retrieval_score = 0.0

            rag_answer = "Internal Error: Knowledge base not found."

        else:

            if " and " in user_query.lower() or "," in user_query:

                query_parts = re.split(r' and |,', user_query.lower())

                query_parts = [p.strip() for p in query_parts if len(p.strip()) > 5]

                seen_ids = set()

                top_part_score = -10.0

                all_part_chunks = []

                for qp in query_parts:

                    part_chunks = retrieve_chunks(qp, index_file, mapping_file, k=10, boost_keywords=boost_kws, section_filter=target_section)

                    if part_chunks:

                        top_part_score = max(top_part_score, part_chunks[0]['score'])

                        for c in part_chunks:

                            if c['chunk_id'] not in seen_ids:

                                all_part_chunks.append(c)

                                seen_ids.add(c['chunk_id'])

                

                                                                      

                all_part_chunks.sort(key=lambda x: x.get('score', 0), reverse=True)

                retrieved_chunks = all_part_chunks

                top_score = top_part_score

            else:

                retrieved_chunks = retrieve_chunks(user_query, index_file, mapping_file, k=20, boost_keywords=boost_kws, section_filter=target_section)

                top_score = retrieved_chunks[0]['score'] if retrieved_chunks else -10.0

            

        if retrieved_chunks:

                                                                     

            

                                                                                    

            retrieval_score = 1.0 / (1.0 + pow(2.718, -(top_score + 2.0)))                

            

                                                                      

            validation_entities = [v for k, v in entities.items() if v and v not in ["...", "TBD", "Low|Medium|High"]]

            query_keywords = [k for k in ["ceo", "cfo", "chairman", "revenue", "policy", "leave", "bonus", "roshni", "nadar", "shiv", "vijaykumar", "leader", "growth", "profit", "ebitda", "dividend", "headcount", "sustainability", "esg", "strategy", "director", "board"] if k in user_query.lower()]

            

            check_list = list(set(validation_entities + query_keywords))

            

            if check_list:

                found_relevant = False

                                                                    

                combined_content = " ".join([c['content'].lower() for c in retrieved_chunks])

                for item in check_list:

                    if item.lower() in combined_content:

                        found_relevant = True

                        break

                

                                                                                                               

                if not found_relevant:

                    retrieval_score *= 0.6 

            print(f"DEBUG: Intent={intent} ({intent_data['confidence']:.2f}), Retrieval Score={retrieval_score:.2f}")

            if retrieval_score >= 0.4: 

                if is_policy_query:

                    combined_content = " ".join([c['content'].lower() for i, c in enumerate(retrieved_chunks) if i < 3])

                    contains_policy_details = any(k in combined_content for k in ["weeks", "days", "months", "eligible", "entitlement", "duration"])

                    contains_financial_terms = any(k in combined_content for k in ["expenditure", "cost", "crore", "budget", "remuneration", "accounting"])

                    

                    if contains_financial_terms and not contains_policy_details:

                        print("Policy query matched financial terms warning.")

                q_idx = (len(history) // 2) + 1 if history else 1

                synthesized = synthesize_answer(user_query, retrieved_chunks)

                rag_answer = f"Question {q_idx}: {user_query}\n{synthesized}"

            else:

                rag_answer = "I could not find this information in the dataset."

        else:

            retrieval_score = 0.0

            rag_answer = "I could not find this information in the dataset."

    policy_decision = decide_next_step(

        intent_data, 

        sentiment_data, 

        entities, 

        retrieval_score=retrieval_score

    )

    

    next_step = policy_decision["next_step"]

    final_output = ""

    

    if next_step == "answer":

        enforced_answer = verify_and_enforce_citations(rag_answer, retrieved_chunks)

        final_output = format_ui_response("answer", enforced_answer)

    elif next_step == "action":

        action_json = generate_action_json(intent, entities)

        final_output = format_ui_response("action", action_json)

    elif next_step == "clarify":

        missing_entities = policy_decision.get("missing_entities", [])

        if missing_entities:

            clarification = generate_clarification(missing_entities)

            final_output = format_ui_response("clarify", clarification)

        else:

            final_output = "I'm here to help! Could you please tell me more about what you need?"

    elif next_step == "escalate":

        reason = policy_decision.get("reason", "Urgency or missing information.")

        final_output = f"I am escalating this request to a human agent. Reason: {reason}"

    

    return final_output

if __name__ == "__main__":

    query = sys.argv[1] if len(sys.argv) > 1 else "What was the revenue growth in FY25?"

    try:

        result = run_pipeline(query, history=[])

        print(f"\n--- OUTPUT ---\n{result}\n--------------\n")

    except Exception as e:

        print(f"Error: {e}")

