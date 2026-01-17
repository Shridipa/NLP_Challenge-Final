import json

import sys

import re

from transformers import pipeline

ner_classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")

def extract_entities(query):
    if isinstance(query, list): query = " ".join([str(x) for x in query])
    if isinstance(query, dict): query = query.get("text", str(query))
    if not isinstance(query, str): query = str(query)
    if not query or not query.strip():

        return {

            "employee_id": "...",

            "department": "...",

            "policy_title": "...",

            "metric": "...",

            "date": "...",

            "application_name": "...",

            "ticket_type": "...",

            "description": "...", 

            "priority": "Medium",

            "topic": "...",

            "participants": "..."

        }

    entities = {

        "employee_id": "...",

        "department": "...",

        "policy_title": "...",

        "metric": "...",

        "date": "...",

        "application_name": "...",

        "ticket_type": "...",

        "description": "...", 

        "priority": "Low|Medium|High",

        "topic": "...",

        "participants": "..."

    }

    emp_id_match = re.search(r'\b(EMP|HCL)\d+\b', query, re.IGNORECASE)

    if emp_id_match:

        entities["employee_id"] = emp_id_match.group(0).upper()

    if re.search(r'\bhigh\b', query, re.IGNORECASE):

        entities["priority"] = "High"

    elif re.search(r'\bmedium\b', query, re.IGNORECASE):

        entities["priority"] = "Medium"

    elif re.search(r'\blow\b', query, re.IGNORECASE):

        entities["priority"] = "Low"

    else:

        entities["priority"] = "Medium"

    slots_to_fill = {

        "department": ["Finance", "HR", "Engineering", "IT", "Sales", "Marketing", "Legal"],

        "ticket_type": ["Software Issue", "Hardware Issue", "Network Issue", "Access Request"],

        "application_name": ["SAP", "Outlook", "Teams", "Jira", "Workday", "Azure", "AWS", "Salesforce", "ServiceNow", "Slack"],

        "metric": ["Revenue", "Growth", "Headcount", "Turnover", "Profit", "EBITDA", "Margin", "Dividend", "ESG", "Sustainability", "Carbon", "Retention"]

    }

    

                                                                          

    likely_slots = []

    if any(k in query.lower() for k in ["issue", "broken", "failed", "repair", "ticket", "not working"]):

        likely_slots.extend(["department", "ticket_type"])

    if any(k in query.lower() for k in ["access", "password", "login", "permission", "account"]):

        likely_slots.extend(["application_name"])

    if any(k in query.lower() for k in ["how many", "what is", "revenue", "profit", "report", "growth", "metric"]):

        likely_slots.extend(["metric"])

        

                                                                 

    slots_to_check = list(set(likely_slots)) if likely_slots else list(slots_to_fill.keys())

    for slot in slots_to_check:

        labels = slots_to_fill[slot]

        result = ner_classifier(query, labels, multi_label=False)

        if result['scores'][0] > 0.65:

            entities[slot] = result['labels'][0]

    date_patterns = [

        (r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', 'DD.MM.YYYY'),

        (r'\b\d{1,2}/\d{1,2}/\d{4}\b', 'DD/MM/YYYY'),

        (r'\b\d{4}-\d{2}-\d{2}\b', 'YYYY-MM-DD'),

        (r'\b\d{1,2}-\d{1,2}-\d{4}\b', 'DD-MM-YYYY'),

        (r'\btomorrow\b', 'relative'),

        (r'\btoday\b', 'relative'),

        (r'\bnext week\b', 'relative'),

        (r'\bnext month\b', 'relative'),

        (r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b', 'Month Day')

    ]

    for pattern, format_type in date_patterns:

        match = re.search(pattern, query, re.IGNORECASE)

        if match:

            entities["date"] = match.group(0)

            break

    meeting_keywords = ['meeting', 'book', 'schedule', 'arrange']

    if any(keyword in query.lower() for keyword in meeting_keywords):

        topic_patterns = [

            r'(?:about|for|regarding|to discuss)\s+([^,\.]+)',

                                                           

        ]

        for pattern in topic_patterns:

            match = re.search(pattern, query, re.IGNORECASE)

            if match:

                entities["topic"] = match.group(1).strip()

                break

        

        if entities["topic"] == "..." and "meeting" in query.lower():

            if len(query.strip().split()) > 3:

                entities["topic"] = query

            else:

                entities["topic"] = "Business Discussion"

    it_keywords = ['broken', 'issue', 'laptop', 'access', 'failed', 'problem', 'reset', 'password', 'slow', 'flickering', 'ticket', 'hardware', 'monitor', 'screen', 'keyboard', 'mouse', 'functioning', 'working', 'help', 'repair', 'fix']

    is_action_like = any(k in query.lower() for k in it_keywords)

    

    if is_action_like and len(query.strip().split()) >= 3:

        entities["description"] = query

    elif "ticket" in query.lower() or "help" in query.lower():

        entities["description"] = "..."

    return entities

if __name__ == "__main__":

    test_query = sys.argv[1] if len(sys.argv) > 1 else "Employee EMP123 from Finance needs to reset password for SAP by tomorrow with high priority"

    try:

        results = extract_entities(test_query)

        print(json.dumps(results, indent=2))

    except Exception as e:

        print(f"Error: {e}")

