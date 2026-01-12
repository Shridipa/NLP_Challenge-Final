import json
import sys
import re
from transformers import pipeline

print(f"Loading global distilled zero-shot pipeline for entity slot-filling...")
ner_classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")

def extract_entities(query):
    """
    Extracts entities relevant to enterprise actions and retrieval filters.
    """
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
        "topic": "...",          # For meetings
        "participants": "..."    # For meetings
    }

    # 1. Regex for Employee ID
    emp_id_match = re.search(r'\b(EMP|HCL)\d+\b', query, re.IGNORECASE)
    if emp_id_match:
        entities["employee_id"] = emp_id_match.group(0).upper()

    # 2. Priority detection
    if re.search(r'\bhigh\b', query, re.IGNORECASE):
        entities["priority"] = "High"
    elif re.search(r'\bmedium\b', query, re.IGNORECASE):
        entities["priority"] = "Medium"
    elif re.search(r'\blow\b', query, re.IGNORECASE):
        entities["priority"] = "Low"
    else:
        entities["priority"] = "Medium"

    # 3. Use Zero-Shot for slots with a fallback option
    slots_to_fill = {
        "department": ["Finance", "HR", "Engineering", "IT", "Sales", "Marketing", "Legal", "Other/General"],
        "ticket_type": ["Software Issue", "Hardware Issue", "Network Issue", "Access Request", "Keyboard/Mouse", "Monitor", "General Problem"],
        "application_name": ["SAP", "Outlook", "Teams", "Jira", "Workday", "Azure", "AWS", "Salesforce", "ServiceNow", "Slack", "None / Not Specified"],
        "metric": ["Revenue", "Growth", "Headcount", "Turnover", "Profit", "EBITDA", "Margin", "None / Not Specified"]
    }
    
    for slot, labels in slots_to_fill.items():
        result = ner_classifier(query, labels, multi_label=False)
        # Use high confidence threshold to avoid bleeding
        if result['scores'][0] > 0.7:
            # Map "None / Not Specified" back to "..."
            val = result['labels'][0]
            if val in ["None / Not Specified", "Other/General"]:
                entities[slot] = "..."
            else:
                entities[slot] = val

    # 4. Enhanced date extraction for multiple formats
    date_patterns = [
        (r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', 'DD.MM.YYYY'),  # 10.01.2026
        (r'\b\d{1,2}/\d{1,2}/\d{4}\b', 'DD/MM/YYYY'),    # 10/01/2026
        (r'\b\d{4}-\d{2}-\d{2}\b', 'YYYY-MM-DD'),        # 2026-01-10
        (r'\b\d{1,2}-\d{1,2}-\d{4}\b', 'DD-MM-YYYY'),    # 10-01-2026
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

    # 5. Extract meeting topic if it's a meeting request
    meeting_keywords = ['meeting', 'book', 'schedule', 'arrange']
    if any(keyword in query.lower() for keyword in meeting_keywords):
        # Try to extract topic (simple heuristic: words after "about", "for", "regarding")
        topic_patterns = [
            r'(?:about|for|regarding|to discuss)\s+([^,\.]+)',
            r'(?:meeting)\s+(?:about|for|with)\s+([^,\.]+)'
        ]
        for pattern in topic_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                entities["topic"] = match.group(1).strip()
                break
        
        # If no specific topic found but it's a meeting, use description
        if entities["topic"] == "..." and "meeting" in query.lower():
            # Don't use query if it's just "schedule a meeting"
            if len(query.strip().split()) > 3:
                entities["topic"] = query
            else:
                entities["topic"] = "Business Discussion"

    # 6. Simple heuristic for description (only if likely an action)
    it_keywords = ['broken', 'broken', 'issue', 'laptop', 'access', 'failed', 'problem', 'reset', 'password', 'slow', 'flickering', 'ticket']
    is_action_like = any(k in query.lower() for k in it_keywords)
    
    if is_action_like and len(query.strip().split()) > 3:
        entities["description"] = query
    elif "ticket" in query.lower():
        entities["description"] = "..." # Ask for details instead of using circular phrase

    return entities

if __name__ == "__main__":
    test_query = sys.argv[1] if len(sys.argv) > 1 else "Employee EMP123 from Finance needs to reset password for SAP by tomorrow with high priority"
    try:
        results = extract_entities(test_query)
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error in extraction: {e}")
