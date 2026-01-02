"""
Debug script for Order Handling Agent
Shows detailed logs of what happens when placing an order
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents.order_handling_agent import OrderHandlingAgent
from database.db_config import SessionLocal
from database.database import MenuItem

print("="*80)
print("  ORDER AGENT DEBUG SCRIPT")
print("="*80)

# Check menu items first
print("\n[STEP 1] Checking menu items in database...")
db = SessionLocal()
menu_items = db.query(MenuItem).all()
print(f"Found {len(menu_items)} menu items:")
for item in menu_items:
    print(f"  - {item.name} (${item.price}) - Available: {item.is_available}")
db.close()

if len(menu_items) == 0:
    print("\nERROR: No menu items in database!")
    print("Please add menu items first using view_database_contents.py")
    sys.exit(1)

print("\n[STEP 2] Testing order agent with a simple order...")
print("Simulating: 'I want to order a Margherita Pizza. My name is John, phone 0612345678'")
print("\n" + "─"*80)

# Create agent with verbose output (using OpenAI)
agent = OrderHandlingAgent(isOffline=False)

# Test input
test_input = "I want to order a Margherita Pizza. My name is John, phone 0612345678"

print("\n[AGENT EXECUTION - WATCH FOR LOOPS]")
print("="*80)

try:
    response = agent.process(test_input)
    print("\n" + "="*80)
    print("[FINAL RESPONSE]")
    print("="*80)
    print(response)
    print("\n✓ Order processing completed successfully!")
    
except Exception as e:
    print("\n" + "="*80)
    print("[ERROR OCCURRED]")
    print("="*80)
    print(f"Error: {e}")
    print("\nThis might indicate:")
    print("  - Agent hit max_iterations (15) - infinite loop")
    print("  - LLM is not following the prompt format correctly")
    print("  - Tool parsing errors")

print("\n" + "="*80)
print("  DEBUG COMPLETE")
print("="*80)
