# LangGraph Customer Support Agent

A LangGraph-based implementation of an 11-stage customer support workflow agent that processes tickets through deterministic and non-deterministic stages with state persistence and MCP server orchestration.

## 🎯 Overview

This agent models a complete customer support workflow using LangGraph, featuring:

- **11 distinct stages** representing the customer support lifecycle
- **State persistence** across all stages using TypedDict
- **MCP server integration** (COMMON for internal logic, ATLAS for external systems)
- **Non-deterministic decision making** in the DECIDE stage
- **Structured payload input/output** processing

## 📋 Workflow Stages

| Stage | Name | Type | Abilities | MCP Server |
|-------|------|------|-----------|------------|
| 1 | INTAKE | Data Entry | `accept_payload` | - |
| 2 | UNDERSTAND | Deterministic | `parse_request_text`, `extract_entities` | COMMON, ATLAS |
| 3 | PREPARE | Deterministic | `normalize_fields`, `enrich_records`, `add_flags_calculations` | COMMON, ATLAS |
| 4 | ASK | Human Interaction | `clarify_question` | ATLAS |
| 5 | WAIT | Deterministic | `extract_answer`, `store_answer` | ATLAS, State |
| 6 | RETRIEVE | Deterministic | `knowledge_base_search`, `store_data` | ATLAS, State |
| 7 | DECIDE | **Non-deterministic** | `solution_evaluation`, `escalation_decision`, `update_payload` | COMMON, ATLAS, State |
| 8 | UPDATE | Deterministic | `update_ticket`, `close_ticket` | ATLAS |
| 9 | CREATE | Deterministic | `response_generation` | COMMON |
| 10 | DO | Execution | `execute_api_calls`, `trigger_notifications` | ATLAS |
| 11 | COMPLETE | Data Output | `output_payload` | - |

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- LangGraph
- LangChain

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/langgraph-customer-support-agent.git
cd langgraph-customer-support-agent

Install dependencies:

bash
pip install -r requirements.txt
Run the agent:

bash
python agent.py
Requirements
Create a requirements.txt file with:

txt
langgraph==0.0.33
langchain==0.1.0
langchain-openai==0.0.8
python-dotenv==1.0.0
📁 Project Structure
text
langgraph-customer-support-agent/
├── agent.py                 # Main LangGraph agent implementation
├── agent.config.json        # Agent configuration and stage definitions
├── .env.example            # Environment variables template
├── requirements.txt        # Python dependencies
└── README.md              # This file
🎮 Usage
The agent processes customer support tickets through the complete 11-stage workflow:

Sample Input
python
{
    "customer_name": "John Doe",
    "email": "john.doe@example.com",
    "query": "My order hasn't arrived yet and it's been over a week",
    "priority": "high",
    "ticket_id": "TKT-2024-1001"
}
Sample Output
json
{
  "ticket_id": "TKT-2024-1001",
  "customer": "John Doe",
  "priority": "high",
  "decision": "escalated",
  "solution_score": 60,
  "response": {
    "message": "We're addressing your concern"
  },
  "mcp_calls_made": 14,
  "status": "processing_complete"
}
🔧 Key Features
1. State Management
python
class AgentState(TypedDict):
    customer_name: str
    email: str
    query: str
    priority: str
    ticket_id: str
    extracted_entities: Optional[dict]
    # ... other state fields
2. MCP Server Integration
COMMON Server: Internal logic and calculations

ATLAS Server: External system interactions and data lookups

3. Non-deterministic Decision Making
python
# Stage 7: DECIDE - Dynamic decision based on solution score
if state['solution_score'] < 90:
    state['decision'] = "escalated"
else:
    state['decision'] = "auto_resolve"
📊 Sample Scenarios
The agent includes three test scenarios:

High Priority Delivery Issue - Typically escalates (score < 90)

Medium Priority Login Issue - May auto-resolve (score >= 90)

Low Priority Information Request - Decision based on solution quality

🎥 Demo Output
The agent logs each stage execution:

text
🧩 Stage 1: INTAKE - accept_payload
🧩 Stage 2: UNDERSTAND - MCP calls to COMMON/ATLAS
🧩 Stage 7: DECIDE - Score 60 < 90 → Escalating
✅ FINAL STRUCTURED PAYLOAD: {...}
🔮 Future Enhancements
Real MCP server integration

Actual API calls to external systems

Database persistence for state management

UI interface for human-in-the-loop interactions

Enhanced error handling and retry mechanisms

📝 License
This project is created for assessment purposes.
