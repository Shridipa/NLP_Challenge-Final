import sys
import json

def generate_clarification(missing_entities):
    if not missing_entities:
        return "I'm here to help! Could you please provide more details about your request?"
    
    entity_map = {
        "employee_id": "your Employee ID (e.g., HCL123)",
        "department": "the department involved (e.g., IT, HR, Finance)",
        "description": "a description of the issue or request",
        "application_name": "the name of the application (e.g., SAP, Outlook)",
        "date": "the preferred date or time",
        "topic": "the meeting topic",
        "participants": "the attendees for the meeting"
    }
    
    missing_readable = [entity_map.get(e, e.replace("_", " ")) for e in missing_entities]
    
    if len(missing_readable) == 1:
        return f"I need one more detail to proceed. Could you please provide {missing_readable[0]}?"
    else:
        return f"To assist you better, I need a few more details: {', '.join(missing_readable[:-1])} and {missing_readable[-1]}."

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            missing = json.loads(sys.argv[1])
        else:
            missing = ["employee_id", "department"]
        print(generate_clarification(missing))
    except Exception as e:
        print(f"Error: {e}")
