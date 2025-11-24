import os
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


class DatabaseConnector:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = os.getenv('MONGODB_DATABASE', 'customer_service_db')
        
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            
            # Collections
            self.products = self.db['products']
            self.policies = self.db['policies']
            self.orders = self.db['orders']
            
            print(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            self.client = None
            self.db = None
    
    def get_return_policy(self, product_category: str = None) -> Dict[str, Any]:
        
        if not self.db:
            return self._get_default_return_policy()
        
        try:
            query = {"policy_type": "return"}
            if product_category:
                query["category"] = product_category
            
            policy = self.policies.find_one(query)
            
            if policy:
                return {
                    "policy_type": "return",
                    "days_allowed": policy.get('days_allowed', 30),
                    "conditions": policy.get('conditions', []),
                    "refund_percentage": policy.get('refund_percentage', 100),
                    "details": policy.get('details', '')
                }
        except Exception as e:
            print(f"Error fetching return policy: {e}")
        
        return self._get_default_return_policy()
    
    def check_product_returnable(self, product_id: str = None, product_category: str = None) -> Dict[str, Any]:
        
        if not self.db:
            return {"returnable": True, "conditions": ["Within 30 days", "Unused condition"]}
        
        try:
            query = {}
            if product_id:
                query["product_id"] = product_id
            elif product_category:
                query["category"] = product_category
            
            product = self.products.find_one(query)
            
            if product:
                return {
                    "returnable": product.get('returnable', True),
                    "return_window_days": product.get('return_window', 30),
                    "conditions": product.get('return_conditions', []),
                    "restocking_fee": product.get('restocking_fee', 0)
                }
        except Exception as e:
            print(f"Error checking product returnability: {e}")
        
        return {"returnable": True, "return_window_days": 30, "conditions": []}
    
    def calculate_refund(self, order_amount: float, days_since_purchase: int, product_condition: str = "unused") -> Dict[str, Any]:
        
        refund_percentage = 100
        
        # Apply time-based reduction
        if days_since_purchase > 30:
            refund_percentage = 0  
        elif days_since_purchase > 14:
            refund_percentage = 80 
        
        # Apply condition-based reduction
        if product_condition == "used":
            refund_percentage *= 0.9  
        elif product_condition == "damaged":
            refund_percentage *= 0.7 
        
        refund_amount = order_amount * (refund_percentage / 100)
        
        return {
            "original_amount": order_amount,
            "refund_amount": round(refund_amount, 2),
            "refund_percentage": refund_percentage,
            "eligible": refund_percentage > 0,
            "reason": self._get_refund_reason(days_since_purchase, product_condition)
        }
    
    def get_product_info(self, product_id: str = None, 
                        product_name: str = None) -> Optional[Dict[str, Any]]:
        
        if not self.db:
            return None
        
        try:
            query = {}
            if product_id:
                query["product_id"] = product_id
            elif product_name:
                query["name"] = {"$regex": product_name, "$options": "i"}
            
            product = self.products.find_one(query)
            
            if product:
                return {
                    "product_id": product.get('product_id'),
                    "name": product.get('name'),
                    "category": product.get('category'),
                    "price": product.get('price'),
                    "warranty_months": product.get('warranty_months', 12),
                    "returnable": product.get('returnable', True)
                }
        except Exception as e:
            print(f"Error fetching product info: {e}")
        
        return None
    
    def get_damage_protocol(self, damage_type: str = "general") -> Dict[str, Any]:
        
        protocols = {
            "shipping": {
                "action": "full_replacement",
                "requires_photo": True,
                "timeframe": "immediate",
                "refund_option": True,
                "details": "Damaged during shipping - full replacement or refund available"
            },
            "manufacturing": {
                "action": "warranty_replacement",
                "requires_photo": True,
                "timeframe": "3-5 business days",
                "refund_option": True,
                "details": "Manufacturing defect - covered under warranty"
            },
            "user": {
                "action": "paid_repair",
                "requires_photo": True,
                "timeframe": "7-10 business days",
                "refund_option": False,
                "details": "User damage - repair service available at cost"
            },
            "general": {
                "action": "assessment_required",
                "requires_photo": True,
                "timeframe": "3-5 business days",
                "refund_option": True,
                "details": "Damage assessment needed to determine best solution"
            }
        }
        
        return protocols.get(damage_type, protocols["general"])
    
    def _get_default_return_policy(self) -> Dict[str, Any]:
        return {
            "policy_type": "return",
            "days_allowed": 30,
            "conditions": [
                "Product must be unused and in original packaging",
                "All accessories and manuals must be included",
                "Proof of purchase required"
            ],
            "refund_percentage": 100,
            "details": "Full refund available within 30 days of purchase"
        }
    
    def _get_refund_reason(self, days: int, condition: str) -> str:
        """Generate reason for refund calculation."""
        if days > 30:
            return "Return window expired (30 days)"
        elif days > 14:
            return "Partial refund - beyond 14-day full refund window"
        elif condition == "used":
            return "Slight reduction due to used condition"
        elif condition == "damaged":
            return "Reduced refund due to damage"
        else:
            return "Full refund eligible"
    
    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")


# Singleton instance
_db_connector = None

def get_database():
    """Get or create database connector instance."""
    global _db_connector
    if _db_connector is None:
        _db_connector = DatabaseConnector()
    return _db_connector