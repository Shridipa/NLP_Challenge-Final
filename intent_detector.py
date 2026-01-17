import json

import sys

import os

from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")

def detect_intent(query, context=""):
    if isinstance(query, list): query = " ".join([str(x) for x in query])
    if isinstance(query, dict): query = query.get("text", str(query))
    if not isinstance(query, str): query = str(query)
    if not query or not query.strip():

        return {"intent": "other", "confidence": 0.0, "rationale": "Empty query."}

        

    intent_map = {

        "company performance, revenue, financial numbers, annual report statistics": "ask_finance",

        "HR policy, employee benefits, headcount, leave, recruitment": "ask_hr",

        "IT guidelines, security policy, company rules, standards": "ask_it_policy",

        "technical software, code, development, engineering": "ask_dev",

        "technical issue, repair, hardware fix, create IT ticket": "action_ticket",

        "request access, permissions, reset password, login": "action_access",

        "schedule meeting, book calendar, arrange call": "action_schedule",

        "company leaders, board directors, CEO, executives, nadar, vijaykumar": "ask_people",

        "general greeting, conversation, hello, thanks": "other"

    }

    

    candidate_labels = list(intent_map.keys())

    results = classifier(query, candidate_labels)

    

    best_label = results['labels'][0]

    top_intent = intent_map[best_label]

    confidence = results['scores'][0]

    

                                                                                   

    keyword_priorities = {

        "ask_finance": ["revenue", "profit", "ebitda", "cagr", "dividend", "fiscal", "annual report", "finances", "expenditure"],

        "ask_people": ["ceo", "chairman", "chairperson", "vijaykumar", "roshni", "nadar", "director", "executives", "founder", "board of directors"],

        "ask_hr": ["leave", "policy", "employees", "headcount", "recruitment", "payroll"]

    }

    

    query_lower = query.lower()

    for intent_key, keywords in keyword_priorities.items():

        if any(k in query_lower for k in keywords):

                                                                                                        

            if top_intent != intent_key and confidence < 0.85:

                top_intent = intent_key

                confidence = max(confidence, 0.75)

                break

    

    if confidence < 0.7:

        keyword_maps = {

            "ask_people": ["ceo", "cfo", "chairman", "chairperson", "leader", "executive", "founder", "roshni", "nadar", "shiv", "vijaykumar", "management", "directors", "chairwoman", "who is", "who are"],

            "ask_hr": ["policy", "leave", "holiday", "benefit", "payroll", "salary", "pf", "insurance", "hr", "recruitment", "headcount", "employees", "workers"],

            "action_access": ["password", "reset", "access", "login", "permission", "account", "vpn", "mfa", "outlook", "teams"],

            "action_ticket": ["broken", "not working", "fail", "error", "laptop", "monitor", "hardware", "fix", "repair", "ticket", "issue"],

            "ask_finance": ["revenue", "profit", "ebitda", "margin", "growth", "financial", "expenditure", "cost", "dividend", "shareholder", "earnings", "cagr", "turnover"]

        }

        

        override_intent = None

        for intent_key, keywords in keyword_maps.items():

            if any(k in query.lower() for k in keywords):

                override_intent = intent_key

                break

        

        if override_intent:

            top_intent = override_intent

            confidence = 0.85

            rationale = f"Keyword match for '{override_intent}' found."

        else:

            top_intent = "other"

            rationale = f"Low confidence ({confidence:.2f}) and no keyword match."

    else:

        rationale = f"Classified as '{best_label}' with {confidence:.2f} confidence."

    

    return {

        "intent": top_intent,

        "confidence": confidence,

        "rationale": rationale

    }

if __name__ == "__main__":

    test_query = sys.argv[1] if len(sys.argv) > 1 else "What was HCLTech's revenue growth?"

    try:

        result = detect_intent(test_query)

        print(json.dumps(result, indent=2))

    except Exception as e:

        print(f"Error: {e}")

