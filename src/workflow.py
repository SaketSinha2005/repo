import os
from typing import TypedDict, Annotated, Sequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from .schemas import (
    EmailClassification, ProductQuery, EmailResponse, 
    PolicyInfo, ValidationResult
)
from .prompts import EMAIL_CLASSIFICATION_PROMPT, RESPONSE_GENERATION_PROMPT
from .database import get_database

load_dotenv()

class EmailProcessingState(TypedDict):
    email_content: str
    classification: EmailClassification | None
    product_query: ProductQuery | None
    retrieved_context: dict | None
    database_info: dict | None
    generated_response: EmailResponse | None
    validation: ValidationResult | None
    messages: Annotated[Sequence[BaseMessage], "Messages"]
    final_response: str | None
    error: str | None


def get_llm():
    llm_model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
    temperature = float(os.getenv('LLM_TEMPERATURE', '0.3'))
    max_tokens = int(os.getenv('LLM_MAX_TOKENS', '500'))
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    return ChatOpenAI(
        model=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )

try:
    llm = get_llm()
    print(f"LLM initialized: {os.getenv('LLM_MODEL', 'gpt-3.5-turbo')}")
except Exception as e:
    print(f"Error initializing LLM: {e}")
    llm = None

db = get_database()

@tool
def get_return_policy_tool(product_category: str = None) -> dict:
    """Get return policy from database."""
    return db.get_return_policy(product_category)


@tool
def check_product_returnable_tool(product_id: str = None, product_category: str = None) -> dict:
    """Check if product is returnable."""
    return db.check_product_returnable(product_id, product_category)


@tool
def calculate_refund_tool(order_amount: float, days_since_purchase: int, 
                         product_condition: str = "unused") -> dict:
    """Calculate refund amount."""
    return db.calculate_refund(order_amount, days_since_purchase, product_condition)


@tool
def get_damage_protocol_tool(damage_type: str = "general") -> dict:
    """Get damage handling protocol."""
    return db.get_damage_protocol(damage_type)

tools = [get_return_policy_tool, check_product_returnable_tool, 
         calculate_refund_tool, get_damage_protocol_tool]


def classify_query_node(state: EmailProcessingState) -> EmailProcessingState:
    
    if not llm:
        state['error'] = "LLM not initialized. Check API keys OPENAI_API_KEY"
        return state
    
    try:
        print("DEBUG: Entered classify_query_node")
        email = state['email_content']
        
        prompt = f"Classify this customer email into one category: product_return, refund_request, product_damage, or general_inquiry.\n\nEmail: {email}\n\nCategory:"
        
        result = llm.invoke(prompt)
        
        from .schemas import QueryType
        classification = EmailClassification(
            query_type=QueryType.GENERAL,
            confidence=0.9,
            keywords=["general", "inquiry"],
            requires_database_lookup=False,
            reasoning="Default classification for simplified workflow"
        )
        print(f"DEBUG: Created classification: requires_database_lookup={classification.requires_database_lookup}")
        
        state['classification'] = classification
        state['messages'] = state.get('messages', []) + [
            HumanMessage(content=email),
            AIMessage(content="Classified email")
        ]
    
    except Exception as e:
        error_msg = f"Error classifying email: {str(e)}"
        print(f"Error classifying email: {error_msg}")
        state['error'] = error_msg
    
    return state


def retrieve_context_node(state: EmailProcessingState) -> EmailProcessingState:
    
    classification = state['classification']
    
    context = {}
    
    if classification.query_type.value in ["product_return", "refund_request"]:
        policy = get_return_policy_tool.invoke({})
        context['return_policy'] = policy
    
    if classification.query_type.value == "product_damage":
        protocol = get_damage_protocol_tool.invoke({"damage_type": "general"})
        context['damage_protocol'] = protocol
    
    state['retrieved_context'] = context
    state['database_info'] = context 
    return state

def generate_response_node(state: EmailProcessingState) -> EmailProcessingState:
    
    try:
        print("🔍 DEBUG: Entered generate_response_node")
        email = state['email_content']
        classification = state['classification']
        context = state.get('retrieved_context') or {}
        
        policy_info = str(context.get('return_policy', 'Standard policies apply'))
        
        prompt = f"""You are a customer service assistant. Write a professional, helpful response to this customer email.

Customer Email:
{email}

Company Policy:
{policy_info}

Write a professional response:"""
        
        response_text = llm.invoke(prompt).content
        
        response = EmailResponse(
            greeting="Dear Customer,",
            acknowledgment="Thank you for contacting us.",
            main_response=response_text,
            action_items=["We will assist you with your request."],
            closing="Best regards,\nCustomer Service Team",
            tone="friendly",
            full_response=response_text
        )
        
        state['generated_response'] = response
        state['final_response'] = response_text
        
        print(f"Set final_response = {response_text[:50]}...")
    
    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(f"Error generating response: {error_msg}")
        state['error'] = error_msg
        state['final_response'] = "Sorry, we encountered an error generating a response. Please try again later."
    
    return state


def validate_response_node(state: EmailProcessingState) -> EmailProcessingState:
    
    response = state['generated_response']
    
    validation = ValidationResult(
        is_valid=len(response.full_response) > 50,
        issues=[],
        suggestions=[],
        confidence_score=0.9
    )
    
    if not response.greeting:
        validation.issues.append("Missing greeting")
        validation.is_valid = False
    
    if not response.action_items:
        validation.issues.append("No action items specified")
        validation.suggestions.append("Add clear next steps for customer")
    
    state['validation'] = validation
    
    return state


def should_continue(state: EmailProcessingState) -> str:
    
    classification = state.get('classification')
    print(f"DEBUG: should_continue - classification={classification}")  
    
    if not classification:
        print("DEBUG: No classification, returning 'end'")
        return "end"
    
    # If requires database lookup, go to retrieve
    if classification.requires_database_lookup:
        print("DEBUG: Requires DB lookup, returning 'retrieve'")
        return "retrieve"
    else:
        print("DEBUG: No DB lookup needed, returning 'generate'")
        return "generate"


def should_validate(state: EmailProcessingState) -> str:
    
    response = state.get('generated_response')
    
    if response:
        return "validate"
    else:
        return "end"


def create_email_processing_graph():
    
    workflow = StateGraph(EmailProcessingState)
    
    workflow.add_node("classify", classify_query_node)
    workflow.add_node("retrieve", retrieve_context_node)
    workflow.add_node("generate", generate_response_node)
    workflow.add_node("validate", validate_response_node)
    
    workflow.set_entry_point("classify")
    
    workflow.add_conditional_edges(
        "classify",
        should_continue,
        {
            "retrieve": "retrieve",
            "generate": "generate",
            "end": END
        }
    )
    
    workflow.add_edge("retrieve", "generate")
    
    workflow.add_conditional_edges(
        "generate",
        should_validate,
        {
            "validate": "validate",
            "end": END
        }
    )
    
    workflow.add_edge("validate", END)
    
    return workflow.compile()

def process_email(email_content: str) -> dict:
    graph = create_email_processing_graph()
    
    initial_state = EmailProcessingState(
        email_content=email_content,
        classification=None,
        product_query=None,
        retrieved_context=None,
        database_info=None,
        generated_response=None,
        validation=None,
        messages=[],
        final_response=None,
        error=None
    )
    
    try:
        final_state = graph.invoke(initial_state)
        
        print(f"DEBUG: final_response = {final_state.get('final_response')}")
        print(f"DEBUG: error = {final_state.get('error')}")
        
        if final_state.get('error'):
             return {
                "success": False,
                "error": final_state.get('error'),
                "response": "Sorry, we encountered an error processing your request."
            }
        
        classification = final_state.get('classification')
        validation = final_state.get('validation')
        
        return {
            "success": True,
            "response": final_state.get('final_response'),
            "classification": classification.model_dump() if classification else None,
            "validation": validation.model_dump() if validation else None
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": "Sorry, we encountered an error processing your request."
        }


# Export
__all__ = ['process_email', 'create_email_processing_graph', 'EmailProcessingState']


def visualize_graph():
    print("Generating graph visualization...")
    try:
        graph = create_email_processing_graph()
        png_data = graph.get_graph().draw_mermaid_png()
        
        output_path = "workflow_graph/workflow_graph.png"
        with open(output_path, "wb") as f:
            f.write(png_data)
            
        print(f"Graph visualization saved to: {output_path}")
        
    except Exception as e:
        print(f"Error visualizing graph: {e}")

if __name__ == "__main__":
    visualize_graph()

