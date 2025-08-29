import os
import logging
import json
import random
import asyncio
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    customer_name: str
    email: str
    query: str
    priority: str
    ticket_id: str
    extracted_entities: Optional[dict]
    clarification_question: Optional[str]
    clarification_answer: Optional[str]
    kb_data: Optional[dict]
    solution_score: Optional[int]
    decision: Optional[str]
    generated_response: Optional[str]
    mcp_responses: List[dict]

class MCPClient:
    def __init__(self, server_type: str):
        self.server_type = server_type
    
    async def call_ability(self, ability_name: str, input_data: str) -> dict:
        logger.info(f"   - MCP {self.server_type}: {ability_name}")
        await asyncio.sleep(0.3)
        
        responses = {
            "COMMON": {
                "parse_request_text": {"structured_data": "Parssed query", "urgency": "high"},
                "normalize_fields": {"normalized": True, "format": "standard"},
                "add_flags_calculations": {"priority_score": 85, "sla_risk": "medium"},
                "solution_evaluation": {"score": random.randint(40, 100)},
                "response_generation": {"message": "We're addressing your concern"}
            },
            "ATLAS": {
                "extract_entities": {"product": "order", "issue": "delivery_delay"},
                "enrich_records": {"sla": "24h", "history": "2_previous_tickets"},
                "clarify_question": {"question": "Please provide order number"},
                "extract_answer": {"order_number": "12345", "date": "2024-01-15"},
                "knowledge_base_search": {"article": "DEL-442", "content": "3-5 business days"},
                "escalation_decision": {"action": "escalate", "assigned_to": "senior_agent"},
                "update_ticket": {"status": "in_progress", "priority": "high"},
                "close_ticket": {"status": "resolved", "resolution": "completed"},
                "execute_api_calls": {"api": "crm_update", "status": "success"},
                "trigger_notifications": {"notification": "email_sent", "to": "customer"}
            }
        }
        
        result = responses[self.server_type].get(ability_name, {"error": "ability_not_found"})
        logger.info(f"   - Response: {json.dumps(result)[:50]}...")
        return result

common_client = MCPClient("COMMON")
atlas_client = MCPClient("ATLAS")

async def intake_stage(state: AgentState):
    logger.info("\n Stage 1: INTAKE - accept_payload")
    logger.info(f"   - Ticket: {state['ticket_id']}, Priority: {state['priority']}")
    return state

async def understand_stage(state: AgentState):
    logger.info("\n Stage 2: UNDERSTAND")
    parsed = await common_client.call_ability("parse_request_text", state['query'])
    entities = await atlas_client.call_ability("extract_entities", state['query'])
    state['extracted_entities'] = {"parsed": parsed, "entities": entities}
    state['mcp_responses'] = state.get('mcp_responses', []) + [parsed, entities]
    return state

async def prepare_stage(state: AgentState):
    logger.info("\n Stage 3: PREPARE")
    normalized = await common_client.call_ability("normalize_fields", json.dumps(state['extracted_entities']))
    enriched = await atlas_client.call_ability("enrich_records", state['ticket_id'])
    flags = await common_client.call_ability("add_flags_calculations", state['priority'])
    state['extracted_entities'].update({"normalized": normalized, "enriched": enriched, "flags": flags})
    state['mcp_responses'].extend([normalized, enriched, flags])
    return state

async def ask_stage(state: AgentState):
    logger.info("\n Stage 4: ASK")
    question = await atlas_client.call_ability("clarify_question", state['query'])
    state['clarification_question'] = question['question']
    state['mcp_responses'].append(question)
    logger.info("   - ⏸️  Waiting for human response...")
    await asyncio.sleep(1)
    human_response = {"order_number": "12345", "purchase_date": "2024-01-15"}
    state['clarification_answer'] = json.dumps(human_response)
    return state

async def wait_stage(state: AgentState):
    logger.info("\n Stage 5: WAIT")
    extracted = await atlas_client.call_ability("extract_answer", state['clarification_answer'])
    state['mcp_responses'].append(extracted)
    return state

async def retrieve_stage(state: AgentState):
    logger.info("\n Stage 6: RETRIEVE")
    search_data = f"{state['query']} {state['clarification_answer']}"
    kb_result = await atlas_client.call_ability("knowledge_base_search", search_data)
    state['kb_data'] = kb_result
    state['mcp_responses'].append(kb_result)
    return state

async def decide_stage(state: AgentState):
    logger.info("\n Stage 7: DECIDE - Non-deterministic")
    eval_data = f"{state['query']} {state['kb_data']}"
    score_result = await common_client.call_ability("solution_evaluation", eval_data)
    state['solution_score'] = score_result['score']
    state['mcp_responses'].append(score_result)
    
    if state['solution_score'] < 90:
        logger.info(f"   - Score {state['solution_score']} < 90 → Escalating")
        escalation = await atlas_client.call_ability("escalation_decision", str(state['solution_score']))
        state['decision'] = "escalated"
        state['mcp_responses'].append(escalation)
    else:
        logger.info(f"   - Score {state['solution_score']} >= 90 → Auto-resolving")
        state['decision'] = "auto_resolve"
    
    return state

async def update_stage(state: AgentState):
    logger.info("\n Stage 8: UPDATE")
    if state['decision'] == "escalated":
        update_result = await atlas_client.call_ability("update_ticket", state['ticket_id'])
        state['mcp_responses'].append(update_result)
    else:
        close_result = await atlas_client.call_ability("close_ticket", state['ticket_id'])
        state['mcp_responses'].append(close_result)
    return state

async def create_stage(state: AgentState):
    logger.info("\n Stage 9: CREATE")
    response_data = f"{state['query']} Decision: {state['decision']}"
    response = await common_client.call_ability("response_generation", response_data)
    state['generated_response'] = response
    state['mcp_responses'].append(response)
    return state

async def do_stage(state: AgentState):
    logger.info("\n Stage 10: DO")
    api_result = await atlas_client.call_ability("execute_api_calls", state['ticket_id'])
    notify_result = await atlas_client.call_ability("trigger_notifications", state['email'])
    state['mcp_responses'].extend([api_result, notify_result])
    return state

async def complete_stage(state: AgentState):
    logger.info("\n Stage 11: COMPLETE")
    final_payload = {
        "ticket_id": state['ticket_id'],
        "customer": state['customer_name'],
        "priority": state['priority'],
        "decision": state['decision'],
        "solution_score": state['solution_score'],
        "response": state['generated_response'],
        "mcp_calls_made": len(state['mcp_responses']),
        "status": "processing_complete"
    }
    logger.info("\n FINAL STRUCTURED PAYLOAD:")
    print(json.dumps(final_payload, indent=2))
    return state

def create_workflow():
    workflow = StateGraph(AgentState, debug=False)
    stages = [
        ("intake", intake_stage),
        ("understand", understand_stage),
        ("prepare", prepare_stage),
        ("ask", ask_stage),
        ("wait", wait_stage),
        ("retrieve", retrieve_stage),
        ("decide", decide_stage),
        ("update", update_stage),
        ("create", create_stage),
        ("do", do_stage),
        ("complete", complete_stage)
    ]
    for name, func in stages:
        workflow.add_node(name, func)
    workflow.set_entry_point("intake")
    for i in range(len(stages)-1):
        workflow.add_edge(stages[i][0], stages[i+1][0])
    workflow.add_edge("complete", END)
    return workflow.compile()

def get_sample_scenarios():
    return [
        {
            "name": "High Priority Delivery Issue",
            "data": {
                "customer_name": "John Doe",
                "email": "john.doe@example.com",
                "query": "My order hasn't arrived yet and it's been over 10 days. I need urgent help!",
                "priority": "high",
                "ticket_id": "TKT-2024-1001"
            }
        },
        {
            "name": "Medium Priority Login Issue", 
            "data": {
                "customer_name": "Jane Smith",
                "email": "jane.smith@example.com",
                "query": "I can't login to my account, it says invalid credentials when I try",
                "priority": "medium",
                "ticket_id": "TKT-2024-1002"
            }
        },
        {
            "name": "Low Priority Information Request",
            "data": {
                "customer_name": "Bob Wilson",
                "email": "bob.wilson@example.com", 
                "query": "How do I reset my password for the customer portal?",
                "priority": "low",
                "ticket_id": "TKT-2024-1003"
            }
        }
    ]

async def run_workflow_for_scenario(scenario):
    logger.info(f"\n{'='*60}")
    logger.info(f" PROCESSING: {scenario['name']}")
    logger.info(f"{'='*60}")
    
    payload = AgentState(
        **scenario['data'],
        extracted_entities=None,
        clarification_question=None,
        clarification_answer=None,
        kb_data=None,
        solution_score=None,
        decision=None,
        generated_response=None,
        mcp_responses=[]
    )
    
    workflow = create_workflow()
    final_state = await workflow.ainvoke(payload)
    return final_state

async def main():
    logger.info(" LangGraph Customer Support Agent - Assessment Demo")
    logger.info(" Running multiple pre-defined test scenarios...")
    
    scenarios = get_sample_scenarios()
    
    for i, scenario in enumerate(scenarios, 1):
        logger.info(f"\n Scenario {i}/{len(scenarios)}")
        await run_workflow_for_scenario(scenario)
        if i < len(scenarios):
            logger.info("\n" + "═" * 60)
            await asyncio.sleep(2)
    
    logger.info("\n All test scenarios completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())