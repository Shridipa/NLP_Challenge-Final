import sys
import json

def generate_clarification(missing_entities):
    """
    Generates a clarification prompt for missing entities.
    Rules:
    - Ask only one clarifying question at a time.
    - Format: 
      I need one detail to proceed:
      - Missing: {{missing_entities}}
      Question: Please provide {{missing_entities[0]}} to continue.
    """
    if not missing_entities:
        return "No missing entities identified."

    # Format the list of missing entities as a string
    missing_str = ", ".join(missing_entities)
    
    # Take the first missing entity for the specific question
    primary_missing = missing_entities[0]
    
    clarification_msg = (
        f"I need one detail to proceed:\n"
        f"- Missing: {missing_str}\n\n"
        f"Question: Please provide {primary_missing} to continue."
    )
    
    return clarification_msg

if __name__ == "__main__":
    # Test input: list of missing entities as a JSON string
    try:
        if len(sys.argv) > 1:
            missing = json.loads(sys.argv[1])
        else:
            # Default test case
            missing = ["employee_id", "department"]
            
        print(generate_clarification(missing))
    except Exception as e:
        print(f"Error: {e}")
