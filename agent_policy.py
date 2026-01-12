import json
import sys

def decide_next_step(intent_data, sentiment_data, entities, retrieval_score=0.0, coverage_metrics=None):
    """
    Decides the next step based on the agent policy rules.
    """
    intent = intent_data.get("intent", "other")
    confidence = intent_data.get("confidence", 0.0)
    sentiment = sentiment_data.get("sentiment", "neutral")
    is_urgent = sentiment_data.get("is_urgent", False)
    
    # Thresholds
    action_threshold = 0.55 # Minimum confidence for auto-executing actions
    rag_threshold = 0.45    # Minimum retrieval score for RAG answers

    # --- Rule 0: Guardrail Escalation ---
    # If the bot is unsure (low confidence) OR the request is urgent/negative,
    # do NOT try to guess. Escalate immediately if confidence is low.
    if confidence < action_threshold and (is_urgent or sentiment == "negative"):
        return {
            "next_step": "escalate",
            "reason": f"Low confidence ({confidence:.2f}) on urgent/negative request. Escalating for safety."
        }

    # Rule 1: Action Intent Confidence Check
    if intent.startswith("action_") and confidence < action_threshold:
         return {
            "next_step": "clarify",
            "missing_entities": [],
            "reason": f"Action intent confidence ({confidence:.2f}) too low."
        }
    
    # Rule 2: Finance/Strategy Answer (Strong Retrieval Match)
    if intent.startswith("ask_") and retrieval_score >= rag_threshold:
        return {
            "next_step": "answer",
            "missing_entities": [],
            "reason": f"High retrieval score ({retrieval_score:.2f}) for '{intent}'."
        }
        
    # Rule 3: Action generation
    if intent.startswith("action_"):
        # Define required entities per action (minimal requirements)
        required_entities_map = {
            "action_ticket": ["description"], 
            "action_access": ["application_name"], 
            "action_schedule": ["date"]
        }
        
        required = required_entities_map.get(intent, [])
        missing = [e for e in required if not entities.get(e) or entities[e] in ["...", "TBD"]]
        
        if not missing:
            desc = entities.get("description", "")
            app = entities.get("application_name", "...")
            
            # Block if description is too short, vague, or just repeats the intent
            intent_keywords = ["raise a ticket", "create a ticket", "need a ticket", "opening a ticket", "raising a ticket"]
            is_generic = any(ik in desc.lower() for ik in intent_keywords)
            
            if intent == "action_ticket":
                if len(desc) < 25 or is_generic:
                    # If it's generic and we don't have an application name, clarify
                    if app == "...":
                        return {
                            "next_step": "clarify",
                            "missing_entities": ["issue_details"],
                            "reason": f"Description '{desc}' is too generic. Need specific issue details."
                        }
            
            # Additional check for meeting topics
            if intent == "action_schedule" and (len(entities.get("topic", "")) < 5 or "schedule a meeting" in entities.get("topic", "").lower()):
                 return {
                    "next_step": "clarify",
                    "missing_entities": ["meeting_topic"],
                    "reason": "Meeting topic is missing or too vague."
                }

            # Proceed with action if minimum requirements are met
            return {
                "next_step": "action",
                "missing_entities": [],
                "reason": f"Required entities for {intent} are present: {', '.join([f'{k}={v}' for k, v in entities.items() if v not in ['...', 'TBD']])}"
            }
        else:
            # Missing critical entities - ask for clarification
            return {
                "next_step": "clarify",
                "missing_entities": missing,
                "reason": f"Missing required fields for {intent}: {', '.join(missing)}."
            }
            
    # Rule 4: Low retrieval score for knowledge queries
    if intent.startswith("ask_") and retrieval_score < rag_threshold:
        return {
            "next_step": "escalate",
            "missing_entities": [],
            "reason": f"Retrieval score ({retrieval_score:.2f}) too low for reliable grounding."
        }
        
    # Default: Clarify or Other
    return {
        "next_step": "clarify",
        "missing_entities": [],
        "reason": "Intent ambiguous or no specific rule triggered."
    }

if __name__ == "__main__":
    # Test case: Missing entities for ticket
    mock_intent = {"intent": "action_ticket", "confidence": 0.9}
    mock_sentiment = {"sentiment": "neutral", "is_urgent": False}
    mock_entities = {"description": "..."}
    
    result = decide_next_step(mock_intent, mock_sentiment, mock_entities)
    print(json.dumps(result, indent=2))
