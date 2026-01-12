import json
import sys

def generate_action_json(intent, entities):
    """
    Generates a strict JSON action based on intent and entities.
    """
    # Map high-level intent keys to schema-specific action names
    intent_to_action = {
        "action_ticket": "create_ticket",
        "action_access": "request_access",
        "action_schedule": "schedule_meeting"
    }
    
    action_name = intent_to_action.get(intent, "unknown_action")
    
    # Priority default
    priority = entities.get("priority", "Medium")
    if priority == "Low|Medium|High" or not priority:
        priority = "Medium"
        
    # Department default for tickets
    dept = entities.get("department", "...")
    if (dept == "..." or not dept) and action_name == "create_ticket":
        dept = "IT Service Desk"
    elif dept == "..." or not dept:
        dept = "General Support" # Fallback for other actions

    # Construct the JSON structure
    action_json = {
        "action": action_name,
        "department": dept,
        "priority": priority,
    }
    
    # Add action-specific fields
    if action_name == "schedule_meeting":
        action_json["topic"] = entities.get("topic", entities.get("description", "Meeting"))
        action_json["participants"] = entities.get("participants", "TBD")
        action_json["date"] = entities.get("date", "TBD")
        action_json["location"] = entities.get("location", "Virtual")
    else:
        action_json["issue"] = entities.get("description", entities.get("ticket_type", "No description provided"))
    
    # Add context for additional details
    action_json["context"] = {
        "employee_id": entities.get("employee_id", "..."),
        "date": entities.get("date", "..."),
        "application_name": entities.get("application_name", "..."),
        "location": entities.get("location", "Unknown"),
        "device": entities.get("device", "Unknown")
    }
    
    return action_json

if __name__ == "__main__":
    # Test case: Raising a ticket with some entities
    test_intent = "action_ticket"
    test_entities = {
        "employee_id": "EMP123",
        "description": "My laptop screen is flickering",
        "priority": "High"
    }
    
    try:
        # Check if sys.argv provides overrides (mocking pipeline input)
        if len(sys.argv) > 2:
            test_intent = sys.argv[1]
            test_entities = json.loads(sys.argv[2])
            
        result = generate_action_json(test_intent, test_entities)
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        # Strict requirement: Output JSON only (or error in JSON)
        print(json.dumps({"error": str(e)}, indent=2))
