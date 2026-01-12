import gradio as gr
import json
import os
import datetime
from main_assistant import run_pipeline

# Branded assets
LOGO_PATH = r"C:\Users\KIIT\.gemini\antigravity\brain\a9629e95-b346-4d4d-b089-caf1bdf50c37\hcltech_assistant_logo_1767985807080.png"

# Enhanced Custom CSS for the new layout
CUSTOM_CSS = """
.header-area {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #e5e7eb;
}
.header-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
}
.tag-badge {
    background-color: #e0f2fe;
    color: #0369a1;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 99px;
    border: 1px solid #bae6fd;
}
.section-header {
    font-weight: 600;
    color: #334155;
    margin-top: 15px;
    margin-bottom: 5px;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
}
.ticket-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 12px;
    color: white;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.meeting-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 12px;
    color: white;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}
.card-badge {
    background-color: rgba(255, 255, 255, 0.3);
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
}
.card-title {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 6px;
}
.card-detail {
    font-size: 0.85rem;
    opacity: 0.95;
    margin-bottom: 3px;
}
.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #94a3b8;
    font-style: italic;
}
"""

# Storage for tickets and meetings
tickets_storage = []
meetings_storage = []
pending_actions = []

# Helper functions for ticket management
def format_pending_actions_display(actions):
    """Format pending actions for the sidebar"""
    if not actions:
        return "<div class='empty-state'>✨ No pending actions.<br/>Ask the assistant to book something!</div>"
    
    html = ""
    for idx, action in enumerate(actions):
        action_name = action.get('action', 'Action').replace('_', ' ').title()
        html += f"""
        <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid #3b82f6; border-radius: 12px; padding: 12px; margin-bottom: 10px;">
            <div style="font-weight: 700; color: #1e40af; font-size: 0.9rem; margin-bottom: 4px;">🎯 PENDING: {action_name}</div>
            <div style="font-size: 0.8rem; color: #475569;">
                <b>Context:</b> {action.get('topic', action.get('issue', 'General Request'))[:40]}...
            </div>
            <div style="display: flex; gap: 8px; margin-top: 8px;">
                <span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.7rem;">Action #{idx+1}</span>
            </div>
        </div>
        """
    return html

def confirm_action(index):
    """Confirm a pending action and move it to permanent storage"""
    try:
        idx = int(index) - 1
        if 0 <= idx < len(pending_actions):
            action = pending_actions.pop(idx)
            action_type = action.get("action", "")
            
            if action_type == "schedule_meeting":
                meetings_storage.append(action)
                msg = f"✅ Meeting '{action.get('topic')}' confirmed and scheduled!"
            elif action_type == "create_ticket":
                tickets_storage.append(action)
                msg = f"✅ Ticket '{action.get('issue')}' confirmed and logged!"
            else:
                msg = "✅ Action confirmed!"
                
            return msg, format_pending_actions_display(pending_actions), format_meetings_display(meetings_storage), format_tickets_display(tickets_storage)
        return "❌ Invalid action index", format_pending_actions_display(pending_actions), format_meetings_display(meetings_storage), format_tickets_display(tickets_storage)
    except:
        return "❌ Error confirming action", format_pending_actions_display(pending_actions), format_meetings_display(meetings_storage), format_tickets_display(tickets_storage)

def clear_all_pending():
    """Clear all pending actions"""
    pending_actions.clear()
    return "🗑️ All pending actions cleared.", format_pending_actions_display(pending_actions)

def format_tickets_display(tickets):
    """Format tickets for display in the management tab"""
    if not tickets:
        return "<div class='empty-state'>📂 No tickets booked yet.<br/>Use the chat or quick form to create one!</div>"
    
    html = ""
    for idx, ticket in enumerate(tickets):
        priority_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}.get(ticket.get('priority', 'Medium'), "#6b7280")
        html += f"""
        <div class="ticket-card">
            <div class="card-header">
                <span class="card-badge">#{idx + 1} - {ticket.get('department', 'IT')}</span>
                <span style="background-color: {priority_color}; padding: 3px 8px; border-radius: 8px; font-size: 0.7rem;">
                    {ticket.get('priority', 'Medium')}
                </span>
            </div>
            <div class="card-title">{ticket.get('issue', 'No description')}</div>
            <div class="card-detail">📅 Created: {ticket.get('timestamp', 'N/A')}</div>
            <div class="card-detail">🎫 Status: {ticket.get('status', 'Open')}</div>
        </div>
        """
    return html

def format_meetings_display(meetings):
    """Format meetings for display in the management tab"""
    if not meetings:
        return "<div class='empty-state'>📅 No meetings scheduled yet.<br/>Use the chat or quick form to schedule one!</div>"
    
    html = ""
    for idx, meeting in enumerate(meetings):
        html += f"""
        <div class="meeting-card">
            <div class="card-header">
                <span class="card-badge">#{idx + 1} - Meeting</span>
                <span style="background-color: rgba(255, 255, 255, 0.3); padding: 3px 8px; border-radius: 8px; font-size: 0.7rem;">
                    {meeting.get('date_time', 'TBD')}
                </span>
            </div>
            <div class="card-title">{meeting.get('topic', 'No topic')}</div>
            <div class="card-detail">👥 Participants: {meeting.get('participants', 'N/A')}</div>
            <div class="card-detail">📍 Location: {meeting.get('location', 'Virtual')}</div>
        </div>
        """
    return html

def book_ticket_quick(issue, department, priority):
    """Quick book a ticket from the management tab"""
    if not issue.strip():
        return "⚠️ Please provide an issue description", format_tickets_display(tickets_storage)
    
    ticket = {
        "action": "create_ticket",
        "department": department,
        "issue": issue,
        "priority": priority,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "status": "Open"
    }
    tickets_storage.append(ticket)
    return f"✅ Ticket #{len(tickets_storage)} booked successfully!", format_tickets_display(tickets_storage)

def schedule_meeting_quick(topic, participants, date_time, location):
    """Quick schedule a meeting from the management tab"""
    if not topic.strip():
        return "⚠️ Please provide a meeting topic", format_meetings_display(meetings_storage)
    
    meeting = {
        "action": "schedule_meeting",
        "topic": topic,
        "participants": participants,
        "date_time": date_time,
        "location": location,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
    }
    meetings_storage.append(meeting)
    return f"📅 Meeting #{len(meetings_storage)} scheduled successfully!", format_meetings_display(meetings_storage)

def delete_ticket(index):
    """Delete a ticket by index"""
    try:
        idx = int(index) - 1  # Convert to 0-based index
        if 0 <= idx < len(tickets_storage):
            removed = tickets_storage.pop(idx)
            return f"🗑️ Deleted ticket: {removed.get('issue', 'Unknown')}", format_tickets_display(tickets_storage)
        return "❌ Invalid ticket number", format_tickets_display(tickets_storage)
    except (ValueError, TypeError):
        return "❌ Please enter a valid ticket number", format_tickets_display(tickets_storage)

def delete_meeting(index):
    """Delete a meeting by index"""
    try:
        idx = int(index) - 1  # Convert to 0-based index
        if 0 <= idx < len(meetings_storage):
            removed = meetings_storage.pop(idx)
            return f"🗑️ Deleted meeting: {removed.get('topic', 'Unknown')}", format_meetings_display(meetings_storage)
        return "❌ Invalid meeting number", format_meetings_display(meetings_storage)
    except (ValueError, TypeError):
        return "❌ Please enter a valid meeting number", format_meetings_display(meetings_storage)

def refresh_tickets():
    """Refresh the tickets display"""
    return format_tickets_display(tickets_storage)

def refresh_meetings():
    """Refresh the meetings display"""
    return format_meetings_display(meetings_storage)

def process_interaction(query, history):
    """Process user query through the main assistant"""
    try:
        response = run_pipeline(query, history)
        return response
    except Exception as e:
        return f"Error: {e}"

# Use a soft, friendly theme
theme = gr.themes.Soft(
    primary_hue="blue",
    neutral_hue="slate",
    text_size="sm",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui"]
).set(
    body_background_fill="#ffffff",
    block_background_fill="#ffffff",
    block_border_width="1px",
    block_shadow="0 1px 2px 0 rgba(0, 0, 0, 0.05)"
)

with gr.Blocks(title="HCLTech Assistant") as demo:
    
    # Header Section
    with gr.Row(elem_classes="header-area"):
        with gr.Column(scale=9, min_width=200):
            gr.HTML(f"""
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div>
                        <h1 class="header-title">HCLTech Agentic Assistant</h1>
                        <span class="tag-badge">ENTERPRISE V3.0</span>
                    </div>
                </div>
            """)
        with gr.Column(scale=1):
             pass

    with gr.Row():
        # LEFT COLUMN: Sidebar (25%)
        with gr.Column(scale=2, min_width=250):
            gr.Markdown("### 📌 Enterprise Hub", elem_classes="section-header")
            
            with gr.Accordion("Capabilities & Knowledge", open=True):
                gr.Markdown("""
                **Capabilities:**
                *   ✅ Finance & Strategy RAG
                *   ✅ IT Ticketing Automation
                *   ✅ Meeting Scheduler
                *   ✅ HR Policy Assistant
                *   ✅ Access Management
                
                **Knowledge Base:**
                *   📄 Annual Report 2024–25
                *   🛡 Corporate Data Policies
                *   📚 Employee Handbook
                """)
            
            gr.Markdown("### 🎯 Quick Actions", elem_classes="section-header")
            gr.Markdown("""
            💬 **Chat Examples:**
            - "Book a ticket for laptop repair"
            - "Schedule a meeting with HR"
            - "What's our revenue growth?"
            - "Check SAP access status"
            """)

        # MIDDLE COLUMN: Chat Interface (45%)
        with gr.Column(scale=4):
            gr.Markdown("### 💬 Conversational Assistant")
            chatbot = gr.Chatbot(
                height=500,
                show_label=False,
                avatar_images=(None, "https://cdn-icons-png.flaticon.com/512/4712/4712109.png")
            )
            
            with gr.Row():
                user_input = gr.Textbox(
                    placeholder="Ask me anything or request actions...",
                    scale=8,
                    show_label=False,
                    container=False,
                    autofocus=True
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1)
            
            gr.Examples(
                examples=[
                   "What is the revenue growth for FY25?",
                   "Raise an IT ticket for a broken monitor",
                   "Schedule a meeting with the finance team",
                   "Summarize the HR leave policy"
                ],
                inputs=user_input
            )

        # RIGHT COLUMN: Management Section (30%)
        with gr.Column(scale=3, min_width=300):
            gr.Markdown("### 📊 Management Dashboard", elem_classes="section-header")
            
            with gr.Tabs():
                # PENDING ACTIONS TAB
                with gr.Tab("🎯 Pending Actions"):
                    pending_output = gr.HTML(format_pending_actions_display(pending_actions))
                    
                    with gr.Row():
                        pending_index = gr.Number(label="Action #", precision=0, minimum=1, scale=1)
                        confirm_pending_btn = gr.Button("✅ Confirm", variant="primary", scale=1)
                    
                    action_result_msg = gr.Textbox(label="Result", interactive=False, show_label=False)
                    clear_pending_btn = gr.Button("🗑️ Clear All", size="sm")

                # TICKETS TAB
                with gr.Tab("📂 View Tickets"):
                    tickets_output = gr.HTML(format_tickets_display(tickets_storage))
                    
                    with gr.Accordion("🎫 Quick Book Ticket", open=False):
                        ticket_issue = gr.Textbox(label="Issue Description", placeholder="e.g., Laptop screen not working")
                        ticket_dept = gr.Dropdown(
                            choices=["IT", "HR", "Finance", "Admin", "Facilities"],
                            value="IT",
                            label="Department"
                        )
                        ticket_priority = gr.Radio(
                            choices=["High", "Medium", "Low"],
                            value="Medium",
                            label="Priority"
                        )
                        book_ticket_btn = gr.Button("📝 Book Ticket", variant="primary")
                    
                    ticket_status = gr.Textbox(label="Status", interactive=False, show_label=False)
                    
                    with gr.Row():
                        refresh_tickets_btn = gr.Button("🔄 Refresh", size="sm")
                        delete_ticket_index = gr.Number(label="Ticket #", precision=0, minimum=1)
                        delete_ticket_btn = gr.Button("🗑️ Delete", variant="stop", size="sm")
                
                # MEETINGS TAB
                with gr.Tab("📅 View Meetings"):
                    meetings_output = gr.HTML(format_meetings_display(meetings_storage))
                    
                    with gr.Accordion("📆 Quick Schedule Meeting", open=False):
                        meeting_topic = gr.Textbox(label="Meeting Topic", placeholder="e.g., Q1 Strategy Review")
                        meeting_participants = gr.Textbox(label="Participants", placeholder="e.g., John, Sarah, Mike")
                        meeting_datetime = gr.Textbox(label="Date & Time", placeholder="e.g., 2026-01-15 2:00 PM")
                        meeting_location = gr.Textbox(label="Location", placeholder="e.g., Conference Room A or Zoom", value="Virtual")
                        schedule_meeting_btn = gr.Button("📅 Schedule Meeting", variant="primary")
                    
                    meeting_status = gr.Textbox(label="Status", interactive=False, show_label=False)
                    
                    with gr.Row():
                        refresh_meetings_btn = gr.Button("🔄 Refresh", size="sm")
                        delete_meeting_index = gr.Number(label="Meeting #", precision=0, minimum=1)
                        delete_meeting_btn = gr.Button("🗑️ Delete", variant="stop", size="sm")

    # Event Handlers
    def respond(message, history):
        """Handle chat interactions with streaming effect"""
        # Add user message to history immediately
        history.append({"role": "user", "content": message})
        # Add empty assistant message to be filled
        history.append({"role": "assistant", "content": ""})
        
        # Initial display
        yield "", history, format_pending_actions_display(pending_actions)

        # Get bot response (simulated streaming or word-by-word)
        bot_msg_full = process_interaction(message, history[:-2]) # Pass history without the new pair
        
        # Stream the message word by word for a smooth effect
        words = bot_msg_full.split()
        streaming_msg = ""
        for i, word in enumerate(words):
            streaming_msg += word + " "
            history[-1]["content"] = streaming_msg
            # Update more frequently at start, then slightly slower
            if i < 5 or i % 3 == 0 or i == len(words) - 1:
                yield "", history, format_pending_actions_display(pending_actions)
        
        # After full message is received, check for actions to update dashboard
        try:
            import re
            json_match = re.search(r'```json\s*\n(.*?)\n```', bot_msg_full, re.DOTALL)
            if json_match:
                action_json_str = json_match.group(1)
                action_data = json.loads(action_json_str)
                pending_actions.insert(0, action_data)
                yield "", history, format_pending_actions_display(pending_actions)
        except:
            pass


    # Chat event handlers
    msg_inputs = [user_input, chatbot]
    msg_outputs = [user_input, chatbot, pending_output]
    
    user_input.submit(respond, msg_inputs, msg_outputs)
    submit_btn.click(respond, msg_inputs, msg_outputs)
    
    # Action Confirmation Handlers
    confirm_pending_btn.click(
        confirm_action,
        [pending_index],
        [action_result_msg, pending_output, meetings_output, tickets_output]
    )
    clear_pending_btn.click(
        clear_all_pending,
        None,
        [action_result_msg, pending_output]
    )
    
    # Ticket management handlers
    book_ticket_btn.click(
        book_ticket_quick,
        [ticket_issue, ticket_dept, ticket_priority],
        [ticket_status, tickets_output]
    )
    refresh_tickets_btn.click(refresh_tickets, None, tickets_output)
    delete_ticket_btn.click(delete_ticket, delete_ticket_index, [ticket_status, tickets_output])
    
    # Meeting management handlers
    schedule_meeting_btn.click(
        schedule_meeting_quick,
        [meeting_topic, meeting_participants, meeting_datetime, meeting_location],
        [meeting_status, meetings_output]
    )
    refresh_meetings_btn.click(refresh_meetings, None, meetings_output)
    delete_meeting_btn.click(delete_meeting, delete_meeting_index, [meeting_status, meetings_output])

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1", 
        server_port=7861, 
        allowed_paths=["C:\\"],
        theme=theme,
        css=CUSTOM_CSS
    )
