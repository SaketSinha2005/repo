import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def seed_database():
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    db_name = os.getenv('MONGODB_DATABASE', 'customer_service_db')
    
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    print(f"Connected to {db_name}")
    
    # Clear existing data
    db.products.delete_many({})
    db.policies.delete_many({})
    db.orders.delete_many({})
    
    print("Cleared existing data")
    
    # Sample Products
    products = [
        {
            "product_id": "LAPTOP-001",
            "name": "Premium Laptop 15 inch",
            "category": "electronics",
            "price": 899.99,
            "warranty_months": 24,
            "returnable": True,
            "return_window": 30,
            "return_conditions": ["Unused", "Original packaging", "All accessories included"],
            "restocking_fee": 0
        },
        {
            "product_id": "PHONE-001",
            "name": "Smartphone Pro Max",
            "category": "electronics",
            "price": 1199.99,
            "warranty_months": 12,
            "returnable": True,
            "return_window": 14,
            "return_conditions": ["Unopened box", "Factory seal intact"],
            "restocking_fee": 50
        },
        {
            "product_id": "SHOE-001",
            "name": "Running Shoes Premium",
            "category": "footwear",
            "price": 129.99,
            "warranty_months": 6,
            "returnable": True,
            "return_window": 30,
            "return_conditions": ["Unworn", "Original tags attached"],
            "restocking_fee": 0
        },
        {
            "product_id": "WATCH-001",
            "name": "Smart Watch Sport Edition",
            "category": "electronics",
            "price": 299.99,
            "warranty_months": 12,
            "returnable": True,
            "return_window": 30,
            "return_conditions": ["Unused", "Original packaging"],
            "restocking_fee": 0
        },
        {
            "product_id": "HEADPHONE-001",
            "name": "Wireless Headphones Premium",
            "category": "electronics",
            "price": 249.99,
            "warranty_months": 12,
            "returnable": True,
            "return_window": 30,
            "return_conditions": ["Unused", "Hygiene seal intact"],
            "restocking_fee": 0
        }
    ]
    
    # Policies
    policies = [
        {
            "policy_type": "return",
            "category": "electronics",
            "days_allowed": 30,
            "conditions": [
                "Product must be in original condition",
                "All accessories and packaging must be included",
                "Proof of purchase required",
                "No signs of use or damage"
            ],
            "refund_percentage": 100,
            "details": "Full refund within 30 days for electronics. Some items may have restocking fee."
        },
        {
            "policy_type": "return",
            "category": "footwear",
            "days_allowed": 30,
            "conditions": [
                "Shoes must be unworn",
                "Original tags must be attached",
                "Must be in original box"
            ],
            "refund_percentage": 100,
            "details": "Full refund within 30 days for unworn footwear"
        },
        {
            "policy_type": "refund",
            "category": "general",
            "processing_days": 5,
            "method": "original_payment",
            "details": "Refunds processed within 5-7 business days to original payment method"
        },
        {
            "policy_type": "warranty",
            "category": "electronics",
            "coverage_months": 12,
            "covers": [
                "Manufacturing defects",
                "Hardware failures",
                "Battery issues"
            ],
            "not_covered": [
                "Physical damage",
                "Water damage",
                "Normal wear and tear"
            ],
            "details": "12-month manufacturer warranty on all electronics"
        }
    ]
    
    # Sample Orders (for testing)
    orders = [
        {
            "order_id": "ORD-12345",
            "customer_email": "customer@example.com",
            "product_id": "LAPTOP-001",
            "order_date": datetime(2024, 11, 1),
            "amount": 899.99,
            "status": "delivered"
        },
        {
            "order_id": "ORD-12346",
            "customer_email": "customer2@example.com",
            "product_id": "PHONE-001",
            "order_date": datetime(2024, 11, 15),
            "amount": 1199.99,
            "status": "delivered"
        }
    ]
    
    # Insert data
    db.products.insert_many(products)
    print(f"✅ Inserted {len(products)} products")
    
    db.policies.insert_many(policies)
    print(f"✅ Inserted {len(policies)} policies")
    
    db.orders.insert_many(orders)
    print(f"✅ Inserted {len(orders)} sample orders")
    
    # Create indexes
    db.products.create_index("product_id")
    db.products.create_index("category")
    db.policies.create_index([("policy_type", 1), ("category", 1)])
    db.orders.create_index("order_id")
    
    print("✅ Created indexes")
    
    print("\n" + "="*60)
    print("DATABASE SEEDED SUCCESSFULLY!")
    print("="*60)
    print(f"\nDatabase: {db_name}")
    print(f"Products: {db.products.count_documents({})}")
    print(f"Policies: {db.policies.count_documents({})}")
    print(f"Orders: {db.orders.count_documents({})}")
    
    client.close()


if __name__ == "__main__":
    seed_database()
