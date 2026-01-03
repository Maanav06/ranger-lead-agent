"""
Ranger Lead Agent - Web Interface

Run with: streamlit run app.py
"""

import streamlit as st
import sys
sys.path.insert(0, ".")

from src.agent import run_agent, LeadsResponse, _lead_to_row
from src.tools import write_leads_impl
import re
import pandas as pd
from io import BytesIO

# Page config
st.set_page_config(
    page_title="rangerGPT",
    page_icon="🤠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern CSS with warm desert/western aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Root variables */
    :root {
        --bg-primary: #0f0f0f;
        --bg-secondary: #1a1a1a;
        --bg-card: #242424;
        --accent-gold: #d4a855;
        --accent-copper: #c17f59;
        --accent-sage: #7d9970;
        --text-primary: #f5f5f5;
        --text-secondary: #a0a0a0;
        --border-subtle: #333333;
        --success: #4ade80;
        --warning: #fbbf24;
        --error: #f87171;
    }
    
    /* Global styles */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Outfit', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container */
    .main .block-container {
        max-width: 1200px;
        padding: 2rem 1rem;
    }
    
    /* Hero header */
    .hero-container {
        text-align: center;
        padding: 3rem 1rem;
        margin-bottom: 2rem;
        background: linear-gradient(180deg, rgba(212,168,85,0.1) 0%, transparent 100%);
        border-radius: 24px;
        border: 1px solid var(--border-subtle);
    }
    
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--accent-gold), var(--accent-copper));
        color: var(--bg-primary);
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
        line-height: 1.1;
    }
    
    .hero-title span {
        background: linear-gradient(135deg, var(--accent-gold), var(--accent-copper));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-top: 0.75rem;
        font-weight: 400;
    }
    
    /* Quick actions */
    .quick-actions {
        display: flex;
        gap: 0.75rem;
        justify-content: center;
        flex-wrap: wrap;
        margin-top: 1.5rem;
    }
    
    .quick-btn {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        color: var(--text-primary);
        padding: 0.6rem 1.2rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
    }
    
    .quick-btn:hover {
        background: var(--accent-gold);
        color: var(--bg-primary);
        border-color: var(--accent-gold);
        transform: translateY(-2px);
    }
    
    /* Stats row */
    .stats-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .stat-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent-gold);
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 0.25rem;
    }
    
    /* Lead cards */
    .lead-card {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .lead-card:hover {
        border-color: var(--accent-gold);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(212,168,85,0.1);
    }
    
    .lead-card.qualified {
        border-left: 4px solid var(--success);
    }
    
    .lead-card.not-qualified {
        border-left: 4px solid var(--error);
    }
    
    .lead-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
    }
    
    .lead-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }
    
    .lead-score {
        background: linear-gradient(135deg, var(--accent-gold), var(--accent-copper));
        color: var(--bg-primary);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .lead-reason {
        color: var(--text-secondary);
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
    
    .lead-details {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.75rem;
    }
    
    .lead-detail {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        color: var(--text-primary);
        background: var(--bg-secondary);
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
    }
    
    .lead-detail-icon {
        font-size: 1rem;
    }
    
    .lead-detail a {
        color: var(--accent-gold);
        text-decoration: none;
    }
    
    .lead-detail a:hover {
        text-decoration: underline;
    }
    
    /* Download buttons container */
    .download-container {
        display: flex;
        gap: 0.75rem;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--border-subtle);
    }
    
    /* Chat messages */
    .stChatMessage {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 16px !important;
    }
    
    /* Chat input */
    .stChatInput > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 16px !important;
    }
    
    .stChatInput input {
        color: var(--text-primary) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-gold), var(--accent-copper)) !important;
        color: var(--bg-primary) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(212,168,85,0.3) !important;
    }
    
    .stDownloadButton > button {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
    }
    
    .stDownloadButton > button:hover {
        background: var(--accent-gold) !important;
        color: var(--bg-primary) !important;
        border-color: var(--accent-gold) !important;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 16px;
        padding: 1rem;
    }
    
    [data-testid="stMetricValue"] {
        color: var(--accent-gold) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--accent-gold) !important;
    }
    
    /* Info/Warning/Error boxes */
    .stAlert {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
    }
    
    /* Divider */
    hr {
        border-color: var(--border-subtle) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    
    /* Section headers */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-subtle);
    }
    
    .section-header h3 {
        color: var(--text-primary);
        font-size: 1.25rem;
        font-weight: 600;
        margin: 0;
    }
    
    .section-header .count {
        background: var(--bg-secondary);
        color: var(--text-secondary);
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Summary text */
    .summary-text {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: var(--bg-card);
        border-radius: 12px;
        border-left: 3px solid var(--accent-gold);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 1rem;
        color: var(--text-secondary);
        font-size: 0.8rem;
        margin-top: 2rem;
    }
    
    .footer a {
        color: var(--accent-gold);
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

# Hero section
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">🤠 AI-Powered Lead Generation</div>
    <h1 class="hero-title">ranger<span>GPT</span></h1>
    <p class="hero-subtitle">Find qualified roofing leads with AI. Just ask in plain English.</p>
</div>
""", unsafe_allow_html=True)


def is_lead_search(query: str) -> bool:
    """Detect if query is asking for leads."""
    query_lower = query.lower()
    lead_keywords = ['find', 'get', 'search', 'look for', 'locate', 'list']
    lead_targets = ['inspector', 'realtor', 'agent', 'manager', 'lead', 'homeowner', 'property', 'storm']
    
    has_lead_keyword = any(kw in query_lower for kw in lead_keywords)
    has_lead_target = any(t in query_lower for t in lead_targets)
    
    return has_lead_keyword and has_lead_target


def display_leads(result: LeadsResponse):
    """Display leads in a modern format."""
    
    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Found", result.total_found)
    with col2:
        st.metric("Qualified", result.qualified_count)
    with col3:
        st.metric("With Phone", result.phones_found)
    
    # Summary
    if result.summary:
        st.markdown(f'<div class="summary-text">{result.summary}</div>', unsafe_allow_html=True)
    
    # Storm events notice
    if result.storm_events:
        st.info(f"⛈️ Storm events detected: {', '.join(result.storm_events[:3])}")
    
    # Skip trace warning
    if not result.skip_trace_configured:
        st.warning("⚠️ Skip trace not configured — homeowner phone numbers unavailable")
    
    # Leads section
    st.markdown(f"""
    <div class="section-header">
        <h3>📋 Leads</h3>
        <span class="count">{len(result.leads)}</span>
    </div>
    """, unsafe_allow_html=True)
    
    for i, lead in enumerate(result.leads, 1):
        status_class = "qualified" if lead.qualified else "not-qualified"
        status_icon = "✓" if lead.qualified else "✗"
        
        # Build details HTML
        details = []
        if lead.phone:
            details.append(f'<div class="lead-detail"><span class="lead-detail-icon">📞</span>{lead.phone}</div>')
        if lead.email:
            details.append(f'<div class="lead-detail"><span class="lead-detail-icon">✉️</span><a href="mailto:{lead.email}">{lead.email}</a></div>')
        if lead.website:
            url = lead.website if lead.website.startswith('http') else f'https://{lead.website}'
            details.append(f'<div class="lead-detail"><span class="lead-detail-icon">🌐</span><a href="{url}" target="_blank">{lead.website[:30]}...</a></div>')
        if lead.address:
            details.append(f'<div class="lead-detail"><span class="lead-detail-icon">📍</span>{lead.address}</div>')
        
        details_html = ''.join(details) if details else '<div class="lead-detail">No contact details available</div>'
        
        st.markdown(f"""
        <div class="lead-card {status_class}">
            <div class="lead-header">
                <h4 class="lead-name">{status_icon} {lead.name or lead.address or 'Unknown Lead'}</h4>
                <span class="lead-score">{lead.score}/100</span>
            </div>
            <p class="lead-reason">{lead.reason or 'No qualification reason provided'}</p>
            <div class="lead-details">
                {details_html}
            </div>
        </div>
        """, unsafe_allow_html=True)


def create_excel_download(result: LeadsResponse) -> bytes:
    """Create Excel file in memory for download."""
    if not result.leads:
        return None
    
    data = []
    for lead in result.leads:
        row = _lead_to_row(lead)
        data.append(row.model_dump())
    
    df = pd.DataFrame(data)
    
    # Reorder columns
    priority_cols = ['name', 'phone', 'email', 'address', 'city', 'state', 'type', 'score', 'qualified', 'website']
    existing_priority = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in priority_cols]
    df = df[existing_priority + other_cols]
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    
    return output.getvalue()


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤠"):
        if message.get("leads"):
            display_leads(message["leads"])
        else:
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Try: Find 10 home inspectors in Austin, TX"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    
    # Process query
    with st.chat_message("assistant", avatar="🤠"):
        with st.spinner("🔍 Searching..." if is_lead_search(prompt) else "💭 Thinking..."):
            try:
                if is_lead_search(prompt):
                    result = run_agent(prompt, output_type=LeadsResponse)
                    display_leads(result)
                    
                    # Download buttons
                    if result.leads:
                        excel_data = create_excel_download(result)
                        filename = re.sub(r'[^a-zA-Z0-9\s]', '', prompt).replace(' ', '_')[:30]
                        
                        st.markdown("---")
                        col1, col2, col3 = st.columns([1, 1, 2])
                        with col1:
                            st.download_button(
                                label="📥 Excel",
                                data=excel_data,
                                file_name=f"leads_{filename}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        with col2:
                            rows = [_lead_to_row(lead) for lead in result.leads]
                            df = pd.DataFrame([r.model_dump() for r in rows])
                            csv_data = df.to_csv(index=False)
                            st.download_button(
                                label="📥 CSV",
                                data=csv_data,
                                file_name=f"leads_{filename}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                    # Store in history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result.summary,
                        "leads": result
                    })
                else:
                    response = run_agent(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Footer
st.markdown("""
<div class="footer">
    🤠 rangerGPT • Powered by OpenAI
</div>
""", unsafe_allow_html=True)
