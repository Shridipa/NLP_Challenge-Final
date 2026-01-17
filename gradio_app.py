import gradio as gr
import json
import os
import datetime
import re
from main_assistant import run_pipeline

# Color Palette Variables (from user schema)
INK_BLACK = "#0f1020"  # DEFAULT / 500
DARK_AMETHYST = "#2f195f" # DEFAULT / 500
DEEP_LILAC = "#7353ba" # DEFAULT / 500
PERIWINKLE = "#d8c4ff" # DEFAULT / 500
PLATINUM = "#edf2f4" # DEFAULT / 500

# High Contrast Lighter Variants
WHITE = "#ffffff"
LIGHT_PLATINUM = "#ffffff" 
LIGHT_PERIWINKLE = "#ffffff"

CUSTOM_CSS = f"""
footer {{visibility: hidden}}
#help_text {{
    font-size: 0.8rem !important;
    color: {WHITE} !important;
    opacity: 0.9;
    font-style: italic;
    margin-top: 8px;
    text-align: center;
}}
.header-area {{
    background: linear-gradient(135deg, {DARK_AMETHYST} 0%, #170f27 100%);
    padding: 1.2rem 1.8rem;
    border-radius: 12px;
    margin: 12px;
    border: 1px solid rgba(115, 83, 186, 0.4);
    color: {WHITE};
    display: flex;
    align-items: center;
}}
.header-logo-box {{
    background: white;
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 18px;
    font-size: 2rem;
    box-shadow: 0 0 15px rgba(115, 83, 186, 0.3);
}}
.header-title-container {{
    display: flex;
    flex-direction: column;
}}
.header-title {{
    font-size: 1.5rem !important;
    font-weight: 800 !important;
    color: {WHITE} !important;
    margin: 0 !important;
}}
.header-subtitle {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 4px;
}}
.badge-ai {{
    background: {DEEP_LILAC};
    color: white;
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 900;
    text-transform: uppercase;
}}
.version-text {{
    color: {WHITE};
    font-size: 0.75rem;
    opacity: 0.8;
}}
.main-container {{
    background: {INK_BLACK} !important;
    padding: 10px 15px !important;
}}
.section-header {{
    font-size: 0.85rem !important;
    color: {WHITE} !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 1.8rem 0 1rem 0 !important;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.section-header-text {{
    font-size: 0.85rem !important;
    color: {WHITE} !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}
.kb-card, .sidebar-content {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(216, 196, 255, 0.15);
    border-radius: 10px;
    padding: 12px;
}}
.kb-item, .kb-item * {{
    font-size: 0.9rem;
    color: {WHITE} !important;
    margin: 4px 0;
    opacity: 1 !important;
}}
.kb-item li {{
    margin-bottom: 8px !important;
    margin-left: 20px !important;
    list-style-type: disc !important;
}}
.chat-window {{
    background: rgba(0, 0, 0, 0.3) !important;
    border: 1px solid rgba(115, 83, 186, 0.3) !important;
    border-radius: 14px !important;
}}
.dashboard-card {{
    background: rgba(115, 83, 186, 0.05) !important;
    border: 1px solid rgba(115, 83, 186, 0.4) !important;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}}
.confirm-btn {{
    background: linear-gradient(90deg, {DEEP_LILAC}, {DARK_AMETHYST}) !important;
    border: 1px solid rgba(216, 196, 255, 0.2) !important;
    color: white !important;
    font-weight: 800 !important;
    border-radius: 8px !important;
    box-shadow: 0 0 10px rgba(115, 83, 186, 0.3);
}}
.clear-btn {{
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(216, 196, 255, 0.1) !important;
    color: {WHITE} !important;
    font-size: 0.8rem !important;
    margin-top: 15px !important;
    border-radius: 8px !important;
}}
.footer-text {{
    text-align: center;
    color: {WHITE};
    font-size: 0.8rem;
    opacity: 0.7;
    margin-top: 25px;
    padding-bottom: 25px;
}}
.chatbot-wrap .message.user, .chatbot-wrap .message.user * {{
    background: {DARK_AMETHYST} !important;
    color: {WHITE} !important;
    border-radius: 14px 14px 2px 14px !important;
    border: none !important;
}}
.chatbot-wrap .message.bot, .chatbot-wrap .message.bot * {{
    background: transparent !important;
    color: {WHITE} !important;
}}
.chatbot-wrap .message.bot {{
    background: rgba(115, 83, 186, 0.1) !important;
    border: 1px solid rgba(115, 83, 186, 0.3) !important;
    border-radius: 14px 14px 14px 2px !important;
    padding: 12px 16px !important;
}}
.example-btn {{
    background: rgba(255, 255, 255, 0.07) !important;
    border: 1px solid rgba(216, 196, 255, 0.2) !important;
    color: {WHITE} !important;
    font-size: 0.85rem !important;
    border-radius: 8px !important;
    transition: all 0.2s ease;
}}
.tabs, .tab-nav {{
    background: transparent !important;
    border-bottom: 1px solid rgba(216, 196, 255, 0.2) !important;
}}
.tab-nav button {{
    color: {WHITE} !important;
    font-weight: 700 !important;
    opacity: 0.7;
}}
.tab-nav button.selected {{
    color: {WHITE} !important;
    opacity: 1;
    border-bottom: 3px solid {DEEP_LILAC} !important;
}}
.dashboard-card label {{
    color: {WHITE} !important;
    font-weight: 700 !important;
}}
input, textarea {{
    color: {WHITE} !important;
}}
.action-label {{
    background: {DEEP_LILAC};
    color: white;
    font-size: 0.7rem;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 700;
    text-transform: uppercase;
    display: inline-block;
    margin-bottom: 4px;
}}
"""

tickets_storage = []
meetings_storage = []
pending_actions = []

def format_pending_actions_display(actions):
    if not actions:
        return f"<div style='text-align:center; padding:40px; color:{PERIWINKLE}; opacity:0.5; font-size:0.9rem;'>✨ No pending actions.<br>Ask the assistant to book something!</div>"
    html = ""
    for idx, action in enumerate(actions):
        action_name = action.get('action', 'Action').replace('_', ' ').title()
        html += f"""
        <div style="background: rgba(115, 83, 186, 0.1); border: 1px solid {DEEP_LILAC}; border-left: 5px solid {DEEP_LILAC}; border-radius: 12px; padding: 15px; margin-bottom: 12px;">
            <div style="font-weight: 800; color: {PERIWINKLE}; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 6px;">Action #{idx+1}: {action_name}</div>
            <div style="font-size: 0.95rem; color: {PLATINUM}; line-height: 1.4;">
                {action.get('topic', action.get('issue', 'General Request'))[:60]}
            </div>
        </div>
        """
    return html

def confirm_action(index):
    try:
        idx = int(index) - 1
        if 0 <= idx < len(pending_actions):
            action = pending_actions.pop(idx)
            if action.get("action") == "schedule_meeting": meetings_storage.append(action)
            elif action.get("action") == "create_ticket": tickets_storage.append(action)
            return "✅ Confirmed", format_pending_actions_display(pending_actions), format_meetings_display(meetings_storage), format_tickets_display(tickets_storage)
        return "❌ Invalid selection", format_pending_actions_display(pending_actions), format_meetings_display(meetings_storage), format_tickets_display(tickets_storage)
    except: return "❌ Error processing", format_pending_actions_display(pending_actions), format_meetings_display(meetings_storage), format_tickets_display(tickets_storage)

def format_tickets_display(tickets):
    if not tickets: return f"<div style='text-align:center; padding:30px; color:{PERIWINKLE}; opacity:0.6;'>📂 No active tickets</div>"
    html = ""
    for ticket in tickets:
        p = ticket.get('priority', 'Medium').upper()
        html += f"""
        <div class="ticket-card" style="background: rgba(255,255,255,0.05); padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid {DEEP_LILAC};">
            <div style="font-size:0.7rem; color:{PERIWINKLE};">{ticket.get('department')} • {p}</div>
            <div style="font-weight:700; color:{LIGHT_PLATINUM};">{ticket.get('issue')}</div>
        </div>
        """
    return html

def format_meetings_display(meetings):
    if not meetings: return f"<div style='text-align:center; padding:30px; color:{PERIWINKLE}; opacity:0.6;'>📅 No meetings</div>"
    html = ""
    for mt in meetings:
        html += f"""
        <div class="meeting-card" style="background: rgba(255,255,255,0.05); padding:10px; border-radius:8px; margin-bottom:8px; border-left:4px solid {PERIWINKLE};">
            <div style="font-size:0.7rem; color:{PERIWINKLE};">{mt.get('date_time', 'TBD')}</div>
            <div style="font-weight:700; color:{LIGHT_PLATINUM};">{mt.get('topic')}</div>
        </div>
        """
    return html

def respond(message, history):
    if not message: return "", history, format_pending_actions_display(pending_actions)
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ""})
    yield "", history, format_pending_actions_display(pending_actions)
    bot_msg_full = run_pipeline(message, history[:-2])
    words = bot_msg_full.split()
    streaming_msg = ""
    for i, word in enumerate(words):
        streaming_msg += word + " "
        history[-1]["content"] = streaming_msg
        if i % 3 == 0 or i == len(words) - 1: yield "", history, format_pending_actions_display(pending_actions)
    try:
        json_match = re.search(r'```json\s*\n(.*?)\n```', bot_msg_full, re.DOTALL)
        if json_match:
            action_data = json.loads(json_match.group(1))
            pending_actions.insert(0, action_data)
            yield "", history, format_pending_actions_display(pending_actions)
    except: pass

# User Specified Hues
LILAC_HUE = gr.themes.Color(name="lilac", c50="#e3ddf1", c100="#c8bae4", c200="#ac98d6", c300="#9076c8", c400="#7353ba", c500="#5b3e9b", c600="#442e74", c700="#2e1f4d", c800="#170f27", c900="#0f091a", c950="#08050e")
NEUTRAL_HUE = gr.themes.Color(name="ink", c50="#fbfcfd", c100="#edf2f4", c200="#b1c6cf", c300="#759bab", c400="#496a77", c500="#24353b", c600="#0c0d19", c700="#090913", c800="#06060c", c900="#0f1020", c950="#030306")

theme = gr.themes.Soft(primary_hue=LILAC_HUE, neutral_hue=NEUTRAL_HUE, text_size="md", font=[gr.themes.GoogleFont("Outfit"), "sans-serif"]).set(
    body_background_fill=INK_BLACK, block_background_fill=INK_BLACK, block_label_text_color=LIGHT_PERIWINKLE, block_title_text_color=LIGHT_PLATINUM,
    button_primary_background_fill=DEEP_LILAC, button_primary_background_fill_hover="#5b3e9b", button_primary_text_color=LIGHT_PLATINUM,
    border_color_primary=DARK_AMETHYST, input_background_fill="#090913", input_border_color=DARK_AMETHYST,
)

with gr.Blocks(title="HCLTech AI Assistant") as demo:
    # Header Section
    with gr.Row(elem_classes="header-area"):
        gr.HTML(f"""
            <div class="header-logo-box">🧠</div>
            <div class="header-title-container">
                <h1 class="header-title">HCLTech Agentic Assistant</h1>
                <div class="header-subtitle">
                    <span class="badge-ai">AI POWERED</span>
                    <span class="version-text">v3.0.4 • Stable Release</span>
                </div>
            </div>
        """)

    with gr.Row(elem_classes="main-container"):
        # Left Sidebar: Intelligence Hub
        with gr.Column(scale=1):
            gr.HTML("<div class='section-header section-header-text'>🛠 INTELLIGENCE HUB</div>")
            with gr.Accordion("Knowledge Base", open=True):
                gr.HTML(f"""
                    <div class="kb-item">📊 Finance & Strategy RAG</div>
                    <div class="kb-item">🎫 IT Ticketing Automation</div>
                    <div class="kb-item">📅 Meeting Scheduling</div>
                    <div class="kb-item">📜 HR Policy Assistant</div>
                    <div class="kb-item">🔐 Access Management</div>
                """)
            
            gr.HTML("<div class='section-header section-header-text'>💡 QUICK COMMANDS</div>")
            gr.Markdown("- \"Book a laptop repair ticket\"\n- \"Schedule sync with HR team\"\n- \"Analyze FY25 revenue growth\"", elem_classes="kb-item")

        # Center: Conversation
        with gr.Column(scale=3):
            gr.HTML("<div class='section-header section-header-text'>💬 Conversation</div>")
            chatbot = gr.Chatbot(height=520, show_label=False, elem_classes="chat-window chatbot-wrap", value=[{"role": "assistant", "content": "👋 Hello! I am your HCLTech Agentic Assistant. How can I help you today?"}])
            with gr.Row():
                user_input = gr.Textbox(placeholder="Describe your request or ask a question...", scale=10, show_label=False, container=False)
                submit_btn = gr.Button("🚀", variant="primary", scale=1, elem_classes="confirm-btn")
            
            gr.HTML("<div class='section-header section-header-text'>📑 Examples</div>")
            with gr.Row():
                ex1 = gr.Button("What is the revenue growth for FY25?", elem_classes="example-btn")
                ex2 = gr.Button("Raise an IT ticket for Wi-Fi issues", elem_classes="example-btn")
                ex3 = gr.Button("Schedule a meeting for project kickoff", elem_classes="example-btn")

        # Right Panel: Operational Dashboard
        with gr.Column(scale=2):
            gr.HTML("<div class='section-header section-header-text'>📋 OPERATIONAL DASHBOARD</div>")
            with gr.Group(elem_classes="dashboard-card"):
                with gr.Tabs():
                    with gr.Tab("🎯 Pending"):
                        pending_output = gr.HTML(format_pending_actions_display(pending_actions))
                    with gr.Tab("📁 Ticket Registry"):
                        tickets_output = gr.HTML(format_tickets_display(tickets_storage))
                    with gr.Tab("📅 Meeting Logs"):
                        meetings_output = gr.HTML(format_meetings_display(meetings_storage))
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown('<span class="action-label">Action ID</span>', elem_classes="no-padding")
                        pending_index = gr.Number(precision=0, value=0, show_label=False, container=False)
                    with gr.Column(scale=1):
                        gr.HTML('<div style="height: 24px;"></div>')
                        confirm_btn = gr.Button("Confirm", elem_classes="confirm-btn")
                
                gr.Button("🗑 Clear Queue", elem_classes="clear-btn")
                res_msg = gr.Textbox(visible=False)

    # Footer
    gr.HTML("<div class='footer-text'>Use via API • Built with Gradio 🤖 • Settings ⚙️</div>")

    # Event Handlers
    def handle_example(text): return text
    ex1.click(handle_example, [ex1], [user_input])
    ex2.click(handle_example, [ex2], [user_input])
    ex3.click(handle_example, [ex3], [user_input])

    user_input.submit(respond, [user_input, chatbot], [user_input, chatbot, pending_output])
    submit_btn.click(respond, [user_input, chatbot], [user_input, chatbot, pending_output])
    confirm_btn.click(confirm_action, [pending_index], [res_msg, pending_output, meetings_output, tickets_output])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", allowed_paths=["C:\\"], theme=theme, css=CUSTOM_CSS)
