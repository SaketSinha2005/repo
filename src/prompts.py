from langchain.prompts import ChatPromptTemplate, PromptTemplate

SYSTEM_PROMPT = """You are a customer service AI for an e-commerce company. Be professional, empathetic, and helpful."""

EMAIL_CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Classify this customer email:

{email_content}

Categories: product_return, refund_request, product_damage, delivery_issue, product_inquiry, warranty_claim, general, other

Return JSON with: query_type, confidence, keywords, requires_database_lookup, reasoning""")
])

RESPONSE_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Generate a professional response.

Email: {email_content}
Query Type: {query_type}
Policy Info: {policy_info}

Create a helpful response with greeting, acknowledgment, solution, and action items.""")
])
