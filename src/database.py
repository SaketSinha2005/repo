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