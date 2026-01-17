import json
import sys
import re

def format_ui_response(response_type, content):
    if response_type == "answer":
        parts = content.split("--- DETAILED DATA REFERENCES ---")
        main_text = parts[0].strip()
        
        # Extract sources from the end if they exist
        sources = ""
        if "[" in main_text and "Sources:" in main_text:
            s_parts = main_text.split("[Annual Report 2024–25 Sources:")
            if len(s_parts) > 1:
                main_text = s_parts[0].strip()
                sources = f"Annual Report 2024–25 Sources: {s_parts[1].replace(']', '').strip()}"
        
        # Remove redunant Question prefix
        main_text = re.sub(r'Question \d+:.*?\n', '', main_text, flags=re.DOTALL | re.IGNORECASE).strip()
        
        formatted = f"""
        <div class="answer-header">📋 FINANCIAL INSIGHT</div>
        <div class="answer-body">{main_text}</div>
        """
        
        if sources:
            formatted += f'<div class="source-footer">{sources}</div>'
            
        if len(parts) > 1:
            details = parts[1].strip()
            # Clean up details if it has sources at the bottom
            details = re.split(r'\[Annual Report 2024–25 Sources:.*\]', details)[0].strip()
            
            referenced_pages = re.findall(r'\[REF PAGE (\d+)\]', details)
            page_summary = f"Citing {len(referenced_pages)} relevant pages" if referenced_pages else "Full Context"
            
            formatted += f"""
            <div class="reference-container">
                <details>
                    <summary>🔍 {page_summary}</summary>
                    <div class="details-content">{details}</div>
                </details>
            </div>
            """
        return formatted
    elif response_type == "action":
        try:
            if isinstance(content, str):
                json_data = json.loads(content)
            else:
                json_data = content
            action = json_data.get("action", "unknown")
            formatted_json = json.dumps(json_data, indent=2)
            
            if action == "schedule_meeting":
                html = f"""
                <div class="meeting-card">
                    <div class="card-header">
                        <span class="card-badge">MEETING SCHEDULED</span>
                        <span style="font-size: 0.7rem; font-weight: 800; color: #2f195f;">{json_data.get('date', 'TBD')}</span>
                    </div>
                    <div class="card-title">{json_data.get('topic', 'General Meeting')}</div>
                    <div class="card-detail">👥 {json_data.get('participants', 'TBD')}</div>
                </div>
                """
            elif action == "create_ticket":
                html = f"""
                <div class="ticket-card">
                    <div class="card-header">
                        <span class="card-badge">{json_data.get('department', 'IT')} TICKET</span>
                        <span style="font-size: 0.7rem; font-weight: 800; color: #7353ba;">{json_data.get('priority', 'Medium').upper()}</span>
                    </div>
                    <div class="card-title">{json_data.get('issue', 'No description')}</div>
                    <div class="card-detail">📍 Status: INITIALIZED</div>
                </div>
                """
            else:
                html = f'<div class="ticket-card"><div class="card-title">✅ {action.replace("_", " ").title()} Processed</div></div>'
            
            return f"{html}\n\n```json\n{formatted_json}\n```"
        except Exception:
            return str(content)
    elif response_type == "clarify":
        return f"💡 {content}"
    else:
        return content

if __name__ == "__main__":
    pass
