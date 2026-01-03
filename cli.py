#!/usr/bin/env python3
"""
Ranger Lead Agent - Simple Query Interface

Just run: python cli.py
Then type what you want in plain English!
"""

import sys
sys.path.insert(0, ".")

from src.agent import run_agent, LeadsResponse, _lead_to_row
from src.tools import write_leads_impl


def print_banner():
    """Print welcome banner."""
    print()
    print("🤠 LONE RANGER ROOFING - Lead Agent")
    print("=" * 50)
    print()
    print("ASK ANYTHING:")
    print()
    print("  💬 QUESTIONS & STRATEGY")
    print('     "Who can help me find roofing leads?"')
    print('     "What\'s the best way to get referrals?"')
    print('     "How do I find homeowners after a storm?"')
    print()
    print("  🔍 FIND LEADS")
    print('     "Find 10 home inspectors in Austin"')
    print('     "Find storm leads in Texas"')
    print('     "Find realtors near Dallas"')
    print()
    print("'help' = this menu  |  'quit' = exit")
    print("=" * 50)
    print()


def print_leads(result: LeadsResponse):
    """Pretty print leads result."""
    print()
    print(f"📊 {result.summary}")
    print()
    print(f"   Found: {result.total_found} leads")
    print(f"   Qualified: {result.qualified_count}")
    print(f"   With phone: {result.phones_found}")
    
    if not result.skip_trace_configured:
        print("   ⚠️  Skip trace not configured - homeowner phones unavailable")
    
    if result.storm_events:
        print(f"   ⛈️  Storm events: {', '.join(result.storm_events[:3])}")
    
    if result.leads:
        print(f"\n📋 Leads:\n")
        
        for i, lead in enumerate(result.leads, 1):
            status = "✅" if lead.qualified else "❌"
            identifier = lead.name or lead.address or "Unknown"
            
            print(f"{i}. {status} {identifier}")
            print(f"   Score: {lead.score}/100 - {lead.reason}")
            
            if lead.address and lead.name:
                print(f"   📍 {lead.address}")
            
            if lead.phone:
                print(f"   📞 {lead.phone}")
            
            if lead.website:
                print(f"   🌐 {lead.website}")
            
            if lead.email:
                print(f"   ✉️  {lead.email}")
            
            if lead.storm_context:
                print(f"   ⛈️  {lead.storm_context}")
            
            if lead.year_built:
                print(f"   🏠 Built {lead.year_built}")
            
            print()
    else:
        print("\n   No leads found. Try a different search.")


def save_leads(result: LeadsResponse, query: str):
    """Save leads to CSV if any found."""
    if not result.leads:
        return None
    
    rows = [_lead_to_row(lead) for lead in result.leads]
    
    # Create filename from query
    import re
    filename = re.sub(r'[^a-zA-Z0-9\s]', '', query)
    filename = filename.replace(' ', '_')[:40]
    filename = f"leads_{filename}"
    
    response = write_leads_impl(rows, filename)
    return response.filepath if response.success else None


def is_lead_search(query: str) -> bool:
    """Detect if query is asking for leads vs asking a question."""
    query_lower = query.lower()
    
    # Lead search indicators
    lead_keywords = ['find', 'get', 'search', 'look for', 'locate', 'list']
    lead_targets = ['inspector', 'realtor', 'agent', 'manager', 'lead', 'homeowner', 'property', 'storm']
    
    has_lead_keyword = any(kw in query_lower for kw in lead_keywords)
    has_lead_target = any(t in query_lower for t in lead_targets)
    
    return has_lead_keyword and has_lead_target


def process_query(query: str) -> bool:
    """Process a user query. Returns False if should exit."""
    query = query.strip()
    
    if not query:
        return True
    
    if query.lower() in ['quit', 'exit', 'q', 'bye']:
        print("\n👋 Goodbye! Happy hunting! 🤠\n")
        return False
    
    if query.lower() in ['help', '?']:
        print_banner()
        return True
    
    try:
        if is_lead_search(query):
            # Lead search - use structured output
            print(f"\n🔍 Searching for leads...\n")
            result = run_agent(query, output_type=LeadsResponse)
            
            # Print results
            print_leads(result)
            
            # Save to CSV
            filepath = save_leads(result, query)
            if filepath:
                print(f"💾 Saved to: {filepath}")
                print()
        else:
            # Open question - get free-form response
            print(f"\n💭 Thinking...\n")
            response = run_agent(query)  # No output_type = free response
            print(f"\n{response}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Try rephrasing your query.")
    
    return True


def main():
    """Main entry point - interactive query mode."""
    print_banner()
    
    # Check for command line query
    if len(sys.argv) > 1:
        query = ' '.join(sys.argv[1:])
        process_query(query)
        return
    
    # Interactive mode
    while True:
        try:
            query = input("🤠 > ").strip()
            if not process_query(query):
                break
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Goodbye! 🤠\n")
            break


if __name__ == "__main__":
    main()
