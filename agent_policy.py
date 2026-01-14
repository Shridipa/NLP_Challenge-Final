import json
import sys

def decide_next_step(intent_data, sentiment_data, entities, retrieval_score=0.0, coverage_metrics=None):
    """Decides the next step based on the agent policy rules."""
    intent = intent_data.get("intent", "other")
    confidence = intent_data.get("confidence", 0.0)
    sentiment = sentiment_data.get("sentiment", "neutral")
    is_urgent = sentiment_data.get("is_urgent", False)
    
    action_threshold = 0.65
    rag_threshold = 0.50 # This matches the +5.0 shift in query_assistant

    # If it's an ask_ intent, we almost always want to try answering
    if intent.startswith("ask_") and retrieval_score > 1.0:
        return {
            "next_step": "answer",
            "missing_entities": [],
            "reason": f"Grounded informational query with score {retrieval_score:.2f}."
        }

    if (is_urgent or sentiment == "negative") and confidence < 0.4:
        return {
            "next_step": "escalate",
            "reason": f"Urgent/Negative request with very low confidence ({confidence:.2f})."
        }

    if intent.startswith("action_") and confidence < action_threshold:
         return {
            "next_step": "clarify",
            "missing_entities": [],
            "reason": f"Action intent confidence ({confidence:.2f}) too low."
        }
    
    if intent.startswith("ask_") and retrieval_score >= rag_threshold:
        return {
            "next_step": "answer",
            "missing_entities": [],
            "reason": f"High retrieval score ({retrieval_score:.2f}) for '{intent}'."
        }
        
    if intent.startswith("action_"):
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
            
            intent_keywords = ["raise a ticket", "create a ticket", "need a ticket", "opening a ticket", "raising a ticket"]
            is_generic = any(ik in desc.lower() for ik in intent_keywords)
            
            if intent == "action_ticket":
                if len(desc) < 25 or is_generic:
                    if app == "...":
                        return {
                            "next_step": "clarify",
                            "missing_entities": ["issue_details"],
                            "reason": f"Description too generic."
                        }
            
            if intent == "action_schedule" and (len(entities.get("topic", "")) < 5 or "schedule a meeting" in entities.get("topic", "").lower()):
                 return {
                    "next_step": "clarify",
                    "missing_entities": ["meeting_topic"],
                    "reason": "Meeting topic is missing or too vague."
                }

            return {
                "next_step": "action",
                "missing_entities": [],
                "reason": f"Required entities for {intent} are present."
            }
        else:
            return {
                "next_step": "clarify",
                "missing_entities": missing,
                "reason": f"Missing required fields for {intent}: {', '.join(missing)}."
            }
            
    if intent.startswith("ask_") and retrieval_score < rag_threshold:
        return {
            "next_step": "escalate",
            "reason": f"I couldn't find enough reliable information (score: {retrieval_score:.2f}) in the dataset to answer this accurately."
        }
        
    return {
        "next_step": "clarify",
        "missing_entities": [],
        "reason": "Intent ambiguous or no specific rule triggered."
    }

if __name__ == "__main__":
    mock_intent = {"intent": "action_ticket", "confidence": 0.9}
    mock_sentiment = {"sentiment": "neutral", "is_urgent": False}
    mock_entities = {"description": "..."}
    
    result = decide_next_step(mock_intent, mock_sentiment, mock_entities)
    print(json.dumps(result, indent=2))
