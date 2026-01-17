import json

import sys

def generate_action_json(intent, entities):

                                                                      

    intent_to_action = {

        "action_ticket": "create_ticket",

        "action_access": "request_access",

        "action_schedule": "schedule_meeting"

    }

    

    action_name = intent_to_action.get(intent, "unknown_action")

    

    priority = entities.get("priority", "Medium")

    if priority == "Low|Medium|High" or not priority:

        priority = "Medium"

        

    dept = entities.get("department", "...")

    if (dept == "..." or not dept) and action_name == "create_ticket":

        dept = "IT Service Desk"

    elif dept == "..." or not dept:

        dept = "General Support"

    action_json = {

        "action": action_name,

        "department": dept,

        "priority": priority,

    }

    

    import datetime

    

    action_json["timestamp"] = datetime.datetime.now().isoformat()

    action_json["requested_by"] = entities.get("employee_id", "Anonymous")

    

    if action_name == "schedule_meeting":

        action_json["topic"] = entities.get("topic", "Meeting Request")

        action_json["participants"] = entities.get("participants", "TBD")

        action_json["date"] = entities.get("date", "TBD")

        action_json["location"] = entities.get("location", "Virtual")

    else:

        desc = entities.get("description", "...")

        if desc == "..." or not desc:

            desc = entities.get("ticket_type", "General Issue")

        action_json["issue"] = desc

    

    action_json["context"] = {

        "employee_id": entities.get("employee_id", "..."),

        "department": entities.get("department", "..."),

        "application_name": entities.get("application_name", "..."),

        "priority_level": priority

    }

    

    return action_json

if __name__ == "__main__":

    test_intent = "action_ticket"

    test_entities = {

        "employee_id": "EMP123",

        "description": "My laptop screen is flickering",

        "priority": "High"

    }

    

    try:

        if len(sys.argv) > 2:

            test_intent = sys.argv[1]

            test_entities = json.loads(sys.argv[2])

            

        result = generate_action_json(test_intent, test_entities)

        print(json.dumps(result, indent=2))

        

    except Exception as e:

        print(json.dumps({"error": str(e)}, indent=2))

