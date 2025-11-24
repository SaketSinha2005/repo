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
