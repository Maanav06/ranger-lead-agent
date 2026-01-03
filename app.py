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
    page_title="🤠 Lone Ranger Lead Agent",
    page_icon="🤠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .main-header {
        font-size: 2.5rem;
        color: #f39c12;
        text-align: center;
        margin-bottom: 1rem;
    }
    .lead-card {
        background: #1e3a5f;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #f39c12;
    }
    .qualified {
        border-left-color: #27ae60;
    }
    .not-qualified {
        border-left-color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🤠 Lone Ranger Roofing - Lead Agent</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("How to Use")
    st.markdown("""
    **💬 Ask Questions:**
    - "Who can help me find leads?"
    - "What's the best referral strategy?"
    
    **🔍 Find Leads:**
    - "Find 10 home inspectors in Austin"
    - "Find storm leads in Texas"
    - "Find 15 realtors in Dallas"
    """)
    
    st.divider()
    st.header("Settings")
    
    # Model selection
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini (fast)", "gpt-4o (quality)"],
        index=0
    )
    
    st.divider()
    st.caption("📥 Download leads as Excel or CSV")


def is_lead_search(query: str) -> bool:
    """Detect if query is asking for leads."""
    query_lower = query.lower()
    lead_keywords = ['find', 'get', 'search', 'look for', 'locate', 'list']
    lead_targets = ['inspector', 'realtor', 'agent', 'manager', 'lead', 'homeowner', 'property', 'storm']
    
    has_lead_keyword = any(kw in query_lower for kw in lead_keywords)
    has_lead_target = any(t in query_lower for t in lead_targets)
    
    return has_lead_keyword and has_lead_target


def display_leads(result: LeadsResponse):
    """Display leads in a nice format."""
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Found", result.total_found)
    with col2:
        st.metric("Qualified", result.qualified_count)
    with col3:
        st.metric("With Phone", result.phones_found)
    
    st.markdown(f"**Summary:** {result.summary}")
    
    if result.storm_events:
        st.info(f"⛈️ Storm events: {', '.join(result.storm_events[:3])}")
    
    if not result.skip_trace_configured:
        st.warning("⚠️ Skip trace not configured - homeowner phones unavailable")
    
    # Display leads
    st.subheader(f"📋 Leads ({len(result.leads)})")
    
    for i, lead in enumerate(result.leads, 1):
        status = "✅" if lead.qualified else "❌"
        css_class = "qualified" if lead.qualified else "not-qualified"
        
        with st.container():
            st.markdown(f"""
            <div class="lead-card {css_class}">
                <strong>{status} {i}. {lead.name or lead.address or 'Unknown'}</strong><br>
                <small>Score: {lead.score}/100 - {lead.reason}</small>
            </div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(4)
            if lead.phone:
                cols[0].write(f"📞 {lead.phone}")
            if lead.email:
                cols[1].write(f"✉️ {lead.email}")
            if lead.website:
                cols[2].write(f"🌐 {lead.website}")
            if lead.address:
                cols[3].write(f"📍 {lead.address}")


def save_leads(result: LeadsResponse, query: str) -> str:
    """Save leads to CSV and return path."""
    if not result.leads:
        return None
    
    rows = [_lead_to_row(lead) for lead in result.leads]
    filename = re.sub(r'[^a-zA-Z0-9\s]', '', query)
    filename = filename.replace(' ', '_')[:40]
    filename = f"leads_{filename}"
    
    response = write_leads_impl(rows, filename)
    return response.filepath if response.success else None


def create_excel_download(result: LeadsResponse) -> bytes:
    """Create Excel file in memory for download."""
    if not result.leads:
        return None
    
    # Convert leads to dataframe
    data = []
    for lead in result.leads:
        row = _lead_to_row(lead)
        data.append(row.model_dump())
    
    df = pd.DataFrame(data)
    
    # Reorder columns for better UX
    priority_cols = ['name', 'phone', 'email', 'address', 'city', 'state', 'type', 'score', 'qualified', 'website']
    existing_priority = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in priority_cols]
    df = df[existing_priority + other_cols]
    
    # Create Excel in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads')
    
    return output.getvalue()


# Main chat interface
st.subheader("Ask me anything about roofing leads")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("leads"):
            display_leads(message["leads"])
        else:
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Find 10 home inspectors in Austin, TX"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process query
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching..." if is_lead_search(prompt) else "💭 Thinking..."):
            try:
                if is_lead_search(prompt):
                    result = run_agent(prompt, output_type=LeadsResponse)
                    display_leads(result)
                    
                    # Download button for Excel
                    if result.leads:
                        excel_data = create_excel_download(result)
                        filename = re.sub(r'[^a-zA-Z0-9\s]', '', prompt).replace(' ', '_')[:30]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 Download Excel",
                                data=excel_data,
                                file_name=f"leads_{filename}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        with col2:
                            # Also offer CSV
                            rows = [_lead_to_row(lead) for lead in result.leads]
                            df = pd.DataFrame([r.model_dump() for r in rows])
                            csv_data = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv_data,
                                file_name=f"leads_{filename}.csv",
                                mime="text/csv"
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
st.divider()
st.caption("🤠 Lone Ranger Roofing Lead Agent | Results saved to ./output/")

