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
