from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class QueryType(str, Enum):
    """Types of customer queries"""
    PRODUCT_RETURN = "product_return"
    REFUND_REQUEST = "refund_request"
    PRODUCT_DAMAGE = "product_damage"
    DELIVERY_ISSUE = "delivery_issue"
    PRODUCT_INQUIRY = "product_inquiry"
    WARRANTY_CLAIM = "warranty_claim"
    GENERAL = "general"
    OTHER = "other"


class EmailClassification(BaseModel):
    query_type: QueryType = Field(
        description="The type of customer query"
    )
    confidence: float = Field(
        description="Confidence score for the classification (0-1)",
        ge=0.0,
        le=1.0
    )
    keywords: List[str] = Field(
        description="Key phrases or words that helped in classification"
    )
    requires_database_lookup: bool = Field(
        description="Whether this query requires checking the product database"
    )
    reasoning: str = Field(
        description="Brief explanation of why this classification was chosen"
    )


class ProductInfo(BaseModel):
    product_name: Optional[str] = Field(
        default=None,
        description="Name or description of the product mentioned"
    )
    product_id: Optional[str] = Field(
        default=None,
        description="Product ID if mentioned"
    )
    order_number: Optional[str] = Field(
        default=None,
        description="Order number if mentioned"
    )
    purchase_date: Optional[str] = Field(
        default=None,
        description="Purchase date if mentioned"
    )
    issue_description: Optional[str] = Field(
        default=None,
        description="Description of the issue with the product"
    )

class ProductQuery(BaseModel):
    
    customer_name: Optional[str] = Field(
        default=None,
        description="Customer's name if mentioned"
    )
    product_info: ProductInfo = Field(
        description="Information about the product"
    )
    specific_question: str = Field(
        description="The specific question or request from the customer"
    )
    urgency_level: Literal["low", "medium", "high"] = Field(
        description="Urgency level of the request"
    )


class PolicyInfo(BaseModel):
    
    policy_type: str = Field(
        description="Type of policy (return, refund, warranty, etc.)"
    )
    policy_details: str = Field(
        description="Detailed policy information"
    )
    applicable: bool = Field(
        description="Whether this policy applies to the customer's situation"
    )
    conditions: List[str] = Field(
        description="Specific conditions or requirements"
    )


class EmailResponse(BaseModel):
    
    greeting: str = Field(
        description="Personalized greeting"
    )
    acknowledgment: str = Field(
        description="Acknowledgment of the customer's issue"
    )
    main_response: str = Field(
        description="Main body of the response with solution/information"
    )
    action_items: List[str] = Field(
        description="Specific actions the customer should take"
    )
    closing: str = Field(
        description="Professional closing"
    )
    tone: Literal["formal", "friendly", "empathetic"] = Field(
        description="Overall tone of the response"
    )
    full_response: str = Field(
        description="Complete formatted email response"
    )


class DatabaseQuery(BaseModel):
    
    query_type: Literal["return_policy", "refund_amount", "product_info", "warranty_check"] = Field(
        description="Type of database query needed"
    )
    product_id: Optional[str] = None
    product_category: Optional[str] = None
    purchase_date: Optional[str] = None
    condition: Optional[str] = Field(
        default=None,
        description="Product condition (new, damaged, defective, etc.)"
    )


class ValidationResult(BaseModel):
    is_valid: bool = Field(
        description="Whether the response is valid and appropriate"
    )
    issues: List[str] = Field(
        default_factory=list,
        description="List of issues found in the response"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )
    confidence_score: float = Field(
        description="Confidence in the response quality (0-1)",
        ge=0.0,
        le=1.0
    )
