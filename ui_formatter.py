import json
import sys

def format_ui_response(response_type, content):
    """
    Formats the assistant response for the UI.
    Types: answer, action, clarify
    """
    
    if response_type == "answer":
        # Ensure citations are formatted correctly
        # Natural language with inline citations
        return content

    elif response_type == "action":
        # Render a Summary Card and JSON in a code block with a Confirm button
        try:
            if isinstance(content, str):
                json_data = json.loads(content)
            else:
                json_data = content
                
            action_name = json_data.get("action", "General Action").replace("_", " ").title()
            formatted_json = json.dumps(json_data, indent=2)
            
            # Extract key details for user-friendly summary
            action = json_data.get("action", "unknown")
            
            # Create user-friendly summary based on action type
            if action == "schedule_meeting":
                topic = json_data.get("topic", "Meeting")
                date = json_data.get("date", "TBD")
                location = json_data.get("location", "Virtual")
                participants = json_data.get("participants", "...")
                
                summary_card = (
                    f"### Meeting Scheduled Successfully\n\n"
                    f"**Date:** {date}\n"
                    f"**Topic:** {topic}\n"
                    f"**Location:** {location}\n"
                    f"**Participants:** {participants if participants != '...' else 'To be determined'}\n\n"
                    f"---\n\n"
                    f"Your meeting has been added to the system. Type **'yes'** to confirm or provide additional details.\n\n"
                    f"<details>\n<summary>View Full Details (JSON)</summary>\n\n"
                    f"```json\n{formatted_json}\n```\n</details>"
                )
            elif action == "create_ticket":
                issue = json_data.get("issue", "No description")
                priority = json_data.get("priority", "Medium")
                dept = json_data.get("department", "IT")
                
                summary_card = (
                    f"### Ticket Created Successfully\n\n"
                    f"**Issue:** {issue}\n"
                    f"**Priority:** {priority}\n"
                    f"**Department:** {dept}\n\n"
                    f"---\n\n"
                    f"Your ticket has been logged. Type **'yes'** to confirm or provide more details.\n\n"
                    f"<details>\n<summary>View Full Details (JSON)</summary>\n\n"
                    f"```json\n{formatted_json}\n```\n</details>"
                )
            elif action == "request_access":
                # Check top level or context for application name
                app = json_data.get("application_name")
                if not app or app == "...":
                    app = json_data.get("context", {}).get("application_name", "the requested application")
                
                role = json_data.get("role", "Default User")
                
                summary_card = (
                    f"### Access Request Prepared\n\n"
                    f"**Application:** {app}\n"
                    f"**Requested Role:** {role}\n\n"
                    f"---\n\n"
                    f"I have prepared an access request for you. Type **'yes'** to submit it for approval.\n\n"
                    f"<details>\n<summary>View Full Details (JSON)</summary>\n\n"
                    f"```json\n{formatted_json}\n```\n</details>"
                )
            else:
                # Generic action format
                summary_card = (
                    f"### Action Prepared: {action_name}\n"
                    f"**Summary**: I am ready to trigger a {action_name.lower()} with the details provided below.\n\n"
                    f"```json\n{formatted_json}\n```\n\n"
                    "Type **'yes'** to confirm or provide additional information."
                )
            return summary_card
        except Exception as e:
            return f"Error formatting action JSON: {e}"

    elif response_type == "clarify":
        # Single question requesting missing info
        return content

    else:
        return content

if __name__ == "__main__":
    # Test cases via CLI
    try:
        if len(sys.argv) > 2:
            r_type = sys.argv[1]
            r_content = sys.argv[2]
            print(format_ui_response(r_type, r_content))
        else:
            # Demo tests
            print("--- ANSWER UI TEST ---")
            print(format_ui_response("answer", "HCLTech's revenue grew by 6.5%. [Annual Report 2024–25, Page 11]"))
            
            print("\n--- ACTION UI TEST ---")
            action_mock = {"action": "create_ticket", "issue": "Laptop screen flickering"}
            print(format_ui_response("action", action_mock))
            
            print("\n--- CLARIFY UI TEST ---")
            print(format_ui_response("clarify", "Please provide your employee_id to continue."))
    except Exception as e:
        print(f"Error: {e}")
