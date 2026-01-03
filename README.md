# Lone Ranger Roofing - Lead Agent 🤠

Lead qualification agent with **chained reasoning**: Storms → Properties → Contacts → Leads

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHAINED REASONING                            │
└─────────────────────────────────────────────────────────────────┘

  INPUT: "Find leads in Texas"
              │
              ▼
  ┌───────────────────────┐
  │ 1. STORM CHECK        │ → get_nws_alerts("TX")
  │    Hail in Harris Co  │
  └───────────────────────┘
              │
              ▼
  ┌───────────────────────┐
  │ 2. PROPERTY SEARCH    │ → find_open_dataset() + query_socrata()
  │    Older homes found  │
  └───────────────────────┘
              │
              ▼
  ┌───────────────────────┐
  │ 3. CONTACT LOOKUP     │ → skip_trace() for each property
  │    Get owner phones   │   (gracefully fails if not configured)
  └───────────────────────┘
              │
              ▼
  ┌───────────────────────┐
  │ 4. SCORE & OUTPUT     │ → CSV with addresses + phones
  └───────────────────────┘
```

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
cp env.example .env
# Edit .env with your OPENAI_API_KEY

# Test tools
python cli.py test

# Find leads
python cli.py storms -s TX                    # Storm-based leads
python cli.py leads -l "Austin, TX" --storms  # Leads with storm check
python cli.py middlemen -r "home inspector" -l "Austin, TX"
```

## Commands

```bash
# Find homeowner leads (chains: storms → properties → contacts)
python cli.py leads -l "Austin, TX" -t homeowner

# Find leads with storm check first
python cli.py leads -l TX -t homeowner --storms

# Find leads from storm activity (full chain)
python cli.py storms -s TX

# Find middlemen (inspectors, realtors, PMs)
python cli.py middlemen -r "home inspector" -l "Austin, TX"

# Interactive chat
python cli.py chat
```

## Output

```
┌──────────────────────┬─────────────────┬──────────────┬───────┬───────────┐
│ address              │ owner_name      │ phone        │ score │ storm     │
├──────────────────────┼─────────────────┼──────────────┼───────┼───────────┤
│ 123 Oak St, Austin   │ John Smith      │ 512-555-1234 │ 85    │ Hail 1/2  │
│ 456 Elm Ave, Houston │ Jane Doe        │ 713-555-5678 │ 78    │ Wind 1/3  │
│ 789 Pine Rd, Dallas  │ (not available) │ ❌           │ 65    │ None      │
└──────────────────────┴─────────────────┴──────────────┴───────┴───────────┘
```

## Configuration

### Required
```env
OPENAI_API_KEY=sk-your-key-here
```

### Optional - Skip Tracing (for homeowner phones)
```env
# Provider: batchskiptracing or reiskip
SKIP_TRACE_PROVIDER=batchskiptracing
BATCH_SKIP_TRACING_API_KEY=your-key-here
```

If skip tracing is not configured:
- ✅ Agent still works
- ✅ Finds properties and addresses
- ❌ Phone numbers will be unavailable (`phone_available=False`)

## Project Structure

```
ranger-lead-agent/
├── cli.py                    # Command line interface
├── env.example               # Environment template
├── src/
│   ├── agent.py              # Single agent with chained reasoning
│   ├── config.py             # Configuration
│   └── tools/
│       ├── weather.py        # get_nws_alerts
│       ├── discovery.py      # find_open_dataset
│       ├── data.py           # geocode, query_socrata
│       ├── skip_trace.py     # skip_trace (phone lookup)
│       └── output.py         # write_leads, generate_message
├── output/                   # Generated CSV files
└── requirements.txt
```

## Tools

| Tool | Purpose | API |
|------|---------|-----|
| `get_nws_alerts` | Storm alerts | NWS (free) |
| `find_open_dataset` | Find city data portals | - |
| `query_socrata` | Query property data | Socrata (free) |
| `geocode` | Address → coordinates | Census (free) |
| `skip_trace` | Address → phone | Paid service |
| `WebSearchTool` | General web search | OpenAI |

## Using as Library

```python
from src.agent import find_leads, find_storm_leads, find_middlemen

# Full chain: storms → properties → contacts
leads = find_storm_leads("TX")

# Find homeowner leads
leads = find_leads("Austin, TX", lead_type="homeowner", check_storms=True)

# Find middlemen
leads = find_middlemen("home inspector", "Austin, TX")

# Access results
for lead in leads.leads:
    print(f"{lead.address}: {lead.phone or 'No phone'}")
```
