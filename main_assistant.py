import json
import sys
import os

# Import components
from intent_detector import detect_intent
from ner_extractor import extract_entities
from sentiment_analyzer import analyze_sentiment_and_urgency
from query_assistant import retrieve_chunks # Fixed import
from agent_policy import decide_next_step
from action_generator import generate_action_json
from clarifier import generate_clarification
from citation_enforcer import verify_and_enforce_citations
from ui_formatter import format_ui_response

def run_pipeline(user_query, history=None):
    """
    Orchestrates the assistant pipeline with optional history for context.
    history format: list of dicts (Gradio 6)
    """
    # Gradio 6 user_input can be a dict: {"text": "...", "files": [...]}
    if isinstance(user_query, dict):
        user_query = user_query.get("text", "")

    print(f"\n--- PROCESSING QUERY: {user_query} ---\n")
    
    # 1. Intent Detection
    intent_data = detect_intent(user_query)
    intent = intent_data["intent"]
    print(f"Detected Intent: {intent} (Confidence: {intent_data['confidence']:.2f})")
    
    # Contextual Intent Logic
    previous_action_intent = None
    historical_entities = {}
    last_assistant_response = None
    conversation_context = []
    
    if history:
        for msg in reversed(history):
            # Gradio history items can be dicts or tuples (legacy)
            if isinstance(msg, dict):
                m = msg
            elif isinstance(msg, (list, tuple)):
                # Convert list [user, assistant] to dict format
                # If it's a tuple from legacy Gradio, msg[0] is user, msg[1] is bot?
                # Actually, our respond function appends {"role": "user", "content": ...}
                # So we should primarily see dicts. But let's be safe.
                # If we encounter a tuple/list, it's likely a single message entry if we are using the new format?
                # No, if previous interactions were tuples, this handles it.
                if len(msg) > 0:
                     m = {"role": "user", "content": msg[0]} # Placeholder logic for legacy
                else: 
                     continue
            else:
                m = msg.__dict__
            
            if m.get("role") == "user":
                user_msg = m["content"]
                
                # Gradio 6 content can be a list of dictionaries (for multimodal)
                if isinstance(user_msg, list):
                    user_msg = " ".join([item["text"] for item in user_msg if item.get("type") == "text"])
                
                if not user_msg: continue
                
                # Store recent conversation context
                conversation_context.insert(0, user_msg)

                # Find the last action intent
                prev_intent_data = detect_intent(user_msg)
                if prev_intent_data["intent"].startswith("action_") and not previous_action_intent:
                    previous_action_intent = prev_intent_data["intent"]
                
                # Collect entities from history - improved merging
                prev_entities = extract_entities(user_msg)
                for k, v in prev_entities.items():
                    # Don't overwrite if we already have a good value
                    if v and v != "..." and v not in ["Low|Medium|High", "TBD"]:
                        if k not in historical_entities or historical_entities[k] in ["...", "TBD", "Low|Medium|High"]:
                            historical_entities[k] = v
            
            elif m.get("role") == "assistant" and not last_assistant_response:
                # Capture the last assistant response to understand context
                last_assistant_response = m["content"]
                    
    # 2. Entity Extraction
    current_entities = extract_entities(user_query)
    
    # Merge historical entities with current ones intelligently
    # This is now handled down-stream in SMART ENTITY MERGING to support topic switching
    # So we just keep current entities for now
    entities = current_entities.copy()
    
    # Detect informational intent EARLY to prevent it being overwritten by previous action context
    informational_keywords = ["who is", "tell me about", "what is", "where is", "how many", "revenue", "about", "goals", "policy", "sustainability", "esg", "cfo", "headcount"]
    is_informational_query = any(k in user_query.lower() for k in informational_keywords)
    
    # Detect if user is simply providing information (short response, likely answering clarification)
    # Be careful: "CFO info" is short but informational.
    is_simple_info_response = False
    query_words = user_query.strip().split()
    if len(query_words) <= 5 and not is_informational_query:
        has_simple_value = any(current_entities.get(key, "...") != "..." for key in ["date", "priority", "department", "employee_id", "application_name"])
        if has_simple_value and intent == "other":
            is_simple_info_response = True

    # CONTEXT ADOPTION LOGIC
    # Only adopt previous action intent if we are NOT making a new informational request
    should_adopt_previous = False
    if previous_action_intent and intent == "other" and not is_informational_query:
        # Check continuation keywords
        continuation_keywords = ["already", "provided", "mentioned", "said", "told you", "gave you"]
        has_continuation = any(k in user_query.lower() for k in continuation_keywords)
        
        if is_simple_info_response or has_continuation or intent_data["confidence"] < 0.4:
            should_adopt_previous = True
            intent = previous_action_intent
            intent_data["intent"] = intent
            intent_data["confidence"] = 0.85

    # SMART ENTITY MERGING (Strictly Scoped)
    # Only merge historical entities if we are staying in the same intent stream
    entities = current_entities.copy()
    
    # Define which entities are ALLOWED to persist across topics (Global Context)
    global_entities = ["employee_id", "department"] 
    
    if should_adopt_previous or (intent.startswith("action_") and previous_action_intent == intent):
        for k, v_hist in historical_entities.items():
            v_curr = entities.get(k, "...")
            # Always merge global entities, or specific entities IF in the same stream
            if (not v_curr or v_curr in ["...", "TBD"]) and v_hist and v_hist not in ["...", "TBD"]:
                entities[k] = v_hist
    else:
        # Only carry forward global entities like employee_id
        for k in global_entities:
            v_hist = historical_entities.get(k)
            v_curr = entities.get(k, "...")
            if (not v_curr or v_curr in ["...", "TBD"]) and v_hist:
                 entities[k] = v_hist
    
    # 3. Sentiment & Urgency
    sentiment_data = analyze_sentiment_and_urgency(user_query)
    
    # 4. Retrieval (if finance/knowledge related)
    retrieval_score = 0.0
    retrieved_chunks = []
    rag_answer = ""
    
    # Detect if query is about a policy or specific guidelines
    is_policy_query = any(k in user_query.lower() for k in ["policy", "guideline", "rules", "terms", "entitlement", "duration"])
    boost_kws = []
    if is_policy_query:
        boost_kws = ["policy", "eligibility", "weeks", "months", "benefit", "guidelines"]
    elif "cfo" in user_query.lower() or "leadership" in user_query.lower():
        boost_kws = ["chief", "officer", "director", "leadership", "management"]

    if intent.startswith("ask_") or is_informational_query:
        if not intent.startswith("ask_"):
            intent = "ask_finance" 
            intent_data["intent"] = intent 
            
        # Resolve absolute paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        index_file = os.path.join(base_dir, "faq_index.faiss")
        mapping_file = os.path.join(base_dir, "chunks_mapping.json")
        
        if not os.path.exists(index_file) or not os.path.exists(mapping_file):
            retrieval_score = 0.0
            rag_answer = "Internal Error: Knowledge base not found."
        else:
            # Dual Retrieval or Single
            if " and " in user_query.lower():
                query_parts = [p.strip() for p in user_query.lower().split(" and ") if len(p.strip()) > 3]
                retrieved_chunks = []
                seen_ids = set()
                for qp in query_parts:
                    part_chunks = retrieve_chunks(qp, index_file, mapping_file, k=4, boost_keywords=boost_kws)
                    if part_chunks:
                        for c in part_chunks:
                            if c['chunk_id'] not in seen_ids:
                                retrieved_chunks.append(c)
                                seen_ids.add(c['chunk_id'])
            else:
                retrieved_chunks = retrieve_chunks(user_query, index_file, mapping_file, k=5, boost_keywords=boost_kws)
                
            if retrieved_chunks:
                retrieval_score = 0.8
                
                # AMBIGUITY DETECTION (Ambiguity check for policies)
                prefix = "Based on the HCLTech report, here are the relevant details:\n\n"
                if is_policy_query:
                    # Check top 2 chunks to be safe
                    combined_content = (retrieved_chunks[0]['content'] + " " + retrieved_chunks[1]['content'] if len(retrieved_chunks) > 1 else retrieved_chunks[0]['content']).lower()
                    
                    # Stricter validation: specific duration/eligibility terms
                    # Removed "policy" from here because "accounting policy" causes false negatives
                    contains_policy_details = any(k in combined_content for k in ["weeks", "days", "months", "eligible", "entitlement", "duration"])
                    
                    contains_financial_terms = any(k in combined_content for k in ["expenditure", "cost", "crore", "budget", "remuneration", "accounting"])
                    
                    # If it looks financial AND strictly doesn't have duration/eligibility info
                    if contains_financial_terms and not contains_policy_details:
                        # Pre-emptively clarify or warn
                        prefix = "The Annual Report 2024–25 primarily mentions this in the context of financial metrics/expenditure (e.g. well-being costs). For specific HR leave duration or eligibility, please refer to the internal HR handbook.\n\n"

                parts = []
                seen_pages = set()
                retrieved_chunks.sort(key=lambda x: x.get('score', 100))
                
                for i, chunk in enumerate(retrieved_chunks[:4]):
                    page_num = chunk['page_number']
                    if page_num in seen_pages: continue
                    seen_pages.add(page_num)
                    
                    content = " ".join(chunk['content'].split())
                    limit = 450
                    if len(content) > limit:
                        last_period = content[:limit].rfind('.')
                        content = content[:last_period+1] if last_period > limit*0.7 else content[:limit-3] + "..."
                    
                    parts.append(f"• {content} [Annual Report 2024–25, Page {page_num}]")
                
                rag_answer = prefix + "\n\n".join(parts)
            else:
                retrieval_score = 0.1
                rag_answer = "I could not find this information in the dataset."

    # 5. Agent Policy Decision
    policy_decision = decide_next_step(
        intent_data, 
        sentiment_data, 
        entities, 
        retrieval_score=retrieval_score
    )
    
    next_step = policy_decision["next_step"]
    
    # 6. Final Execution & Formatting
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
        final_output = "I am escalating this request to a human agent due to its urgency or missing information in my database."
    
    return final_output

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "What was the revenue growth in FY25?"
        
    try:
        # Mocking empty history for CLI test
        result = run_pipeline(query, history=[])
        print("\n--- FINAL ASSISTANT OUTPUT ---")
        print(result)
        print("-------------------------------\n")
    except Exception as e:
        print(f"Pipeline Error: {e}")
