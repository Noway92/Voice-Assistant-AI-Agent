import os
from datetime import datetime
from langchain_ollama import OllamaLLM
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_react_agent, Tool, AgentExecutor
from langchain_core.prompts import PromptTemplate
from .tools.order_tools_sql import (
    create_order_tool,
    add_item_tool,
    update_item_tool,
    remove_item_tool,
    view_order_tool,
    finalize_order_tool,
    check_status_tool,
    cancel_order_tool
)


class OrderHandlingAgent:
    def __init__(self, isOffline=True):
        if isOffline:
            self.llm = OllamaLLM(model="llama3", temperature=0)
        else:
            api_key = os.getenv("API_KEY_OPENAI")
            if not api_key:
                raise ValueError("API_KEY_OPENAI not found in environment variables")
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
        
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self):
        """Create tools for the agent."""
        return [
            Tool(
                name="create_order",
                func=lambda input_str: self._parse_and_create_order(input_str),
                description=(
                    "Create a new order. "
                    "Input should be: 'name: NAME, phone: PHONE, type: TYPE'. "
                    "TYPE can be 'takeaway' or 'delivery'. "
                    "Example: 'name: John Smith, phone: 0612345678, type: takeaway'"
                )
            ),
            Tool(
                name="add_item",
                func=lambda input_str: self._parse_and_add_item(input_str),
                description=(
                    "Add an item to an order. "
                    "Input should be: 'order_id: ID, item: ITEM_NAME, quantity: NUMBER, requests: REQUESTS'. "
                    "Requests is optional. "
                    "Example: 'order_id: 1, item: Margherita Pizza, quantity: 2, requests: extra cheese'"
                )
            ),
            Tool(
                name="update_item",
                func=lambda input_str: self._parse_and_update_item(input_str),
                description=(
                    "Update quantity of an item in an order. Use quantity 0 to remove item. "
                    "Input should be: 'order_id: ID, item: ITEM_NAME, quantity: NUMBER'. "
                    "Example: 'order_id: 1, item: Margherita Pizza, quantity: 3'"
                )
            ),
            Tool(
                name="remove_item",
                func=lambda input_str: self._parse_and_remove_item(input_str),
                description=(
                    "Remove an item from an order. "
                    "Input should be: 'order_id: ID, item: ITEM_NAME'. "
                    "Example: 'order_id: 1, item: Margherita Pizza'"
                )
            ),
            Tool(
                name="view_order",
                func=lambda input_str: self._parse_and_view_order(input_str),
                description=(
                    "View all items in an order with total price. "
                    "Input should be: 'order_id: ID'. "
                    "Example: 'order_id: 1'"
                )
            ),
            Tool(
                name="finalize_order",
                func=lambda input_str: self._parse_and_finalize_order(input_str),
                description=(
                    "Finalize and submit an order to the kitchen. "
                    "Input should be: 'order_id: ID, instructions: INSTRUCTIONS'. "
                    "Instructions is optional. "
                    "Example: 'order_id: 1, instructions: Please prepare quickly'"
                )
            ),
            Tool(
                name="check_order_status",
                func=lambda input_str: self._parse_and_check_status(input_str),
                description=(
                    "Check status of customer's orders. "
                    "Input should be: 'phone: PHONE, order_id: ID' or just 'phone: PHONE' for all orders. "
                    "Example: 'phone: 0612345678' or 'phone: 0612345678, order_id: 1'"
                )
            ),
            Tool(
                name="cancel_order",
                func=lambda input_str: self._parse_and_cancel_order(input_str),
                description=(
                    "Cancel an order. "
                    "Input should be: 'order_id: ID, phone: PHONE'. "
                    "Example: 'order_id: 1, phone: 0612345678'"
                )
            )
        ]
    
    def _parse_and_create_order(self, input_str: str) -> str:
        """Parse input and create order."""
        try:
            input_str = input_str.strip().strip('\"')
            params = self._parse_input(input_str)
            return create_order_tool(
                params['name'],
                params['phone'],
                params.get('type', 'takeaway')
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: name, phone, and type (optional)."
    
    def _parse_and_add_item(self, input_str: str) -> str:
        """Parse input and add item to order."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return add_item_tool(
                int(params['order_id']),
                params['item'],
                int(params['quantity']),
                params.get('requests', '')
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: order_id, item, and quantity."
    
    def _parse_and_update_item(self, input_str: str) -> str:
        """Parse input and update item quantity."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return update_item_tool(
                int(params['order_id']),
                params['item'],
                int(params['quantity'])
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: order_id, item, and quantity."
    
    def _parse_and_remove_item(self, input_str: str) -> str:
        """Parse input and remove item from order."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return remove_item_tool(
                int(params['order_id']),
                params['item']
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: order_id and item."
    
    def _parse_and_view_order(self, input_str: str) -> str:
        """Parse input and view order."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return view_order_tool(int(params['order_id']))
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: order_id."
    
    def _parse_and_finalize_order(self, input_str: str) -> str:
        """Parse input and finalize order."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return finalize_order_tool(
                int(params['order_id']),
                params.get('instructions', '')
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: order_id."
    
    def _parse_and_check_status(self, input_str: str) -> str:
        """Parse input and check order status."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            order_id = int(params['order_id']) if 'order_id' in params and params['order_id'] else None
            return check_status_tool(params['phone'], order_id)
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: phone (and optionally order_id)."
    
    def _parse_and_cancel_order(self, input_str: str) -> str:
        """Parse input and cancel order."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return cancel_order_tool(
                int(params['order_id']),
                params['phone']
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: order_id and phone."
    
    def _parse_input(self, input_str: str) -> dict:
        """Parse input string into parameters."""
        params = {}
        parts = input_str.split(',')
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                params[key.strip().lower()] = value.strip()
        
        return params
    
    def _create_agent(self):
        """Create the ReAct agent with prompt template."""
        template = """You are a helpful restaurant order assistant handling phone orders.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

Use this EXACT format:

Question: the customer's request
Thought: what do I need to do?
Action: [tool name in lowercase]
Action Input: [parameters without quotes]
Observation: [result]
Thought: what's next?
Final Answer: [response to customer]

CRITICAL FORMAT RULES:
- NEVER write "Final Answer:" until you are completely done with ALL actions
- If you call an action, WAIT for Observation before deciding next step
- After Observation, either call ONE MORE action OR write Final Answer (NOT BOTH)
- NO action after "Final Answer:"
- Each line must start with exactly one of: Question, Thought, Action, Action Input, Observation, Final Answer

STRICT RULES - READ CAREFULLY:
1. Each tool can be called multiple times if needed (unlike reservation agent)
2. ALWAYS create_order FIRST before adding items
3. ALWAYS extract and remember the order_id from create_order Observation
4. When customer says "that's all" or "finish order", use finalize_order
5. Store the order_id in your working memory for the entire conversation

WORKFLOWS:

A) Customer wants to PLACE a new order:
Step 1: Extract name and phone from Question
Step 2: create_order → Wait for Observation → Extract order_id
Step 3: Ask what they want to order (or if already provided, add items)
Step 4: For each item mentioned: add_item → Wait for Observation
Step 5: When customer confirms order is complete: view_order to confirm
Step 6: finalize_order → Wait for Observation → Final Answer

B) Customer wants to ADD items to current order:
Step 1: Use the order_id from memory
Step 2: add_item for each item → Wait for Observation after each
Step 3: Final Answer confirming items added

C) Customer wants to MODIFY order (change quantity or remove):
Step 1: Use update_item or remove_item with order_id
Step 2: Wait for Observation
Step 3: Final Answer confirming change

D) Customer wants to SEE/REPEAT their order:
Step 1: view_order with order_id → Wait for Observation
Step 2: Final Answer with full order details

E) Customer wants to CHECK order status:
Step 1: Extract phone (and order_id if provided)
Step 2: check_order_status → Wait for Observation
Step 3: Final Answer with status

F) Customer wants to CANCEL order:
Step 1: Extract order_id and phone
Step 2: cancel_order → Wait for Observation
Step 3: Final Answer confirming cancellation

Action Input format (NO quotes, NO placeholders):
- create_order: name: John Smith, phone: 0612345678, type: takeaway
- add_item: order_id: 1, item: Margherita Pizza, quantity: 2, requests: extra cheese
- update_item: order_id: 1, item: Margherita Pizza, quantity: 3
- remove_item: order_id: 1, item: Coke
- view_order: order_id: 1
- finalize_order: order_id: 1, instructions: Please prepare quickly
- check_order_status: phone: 0612345678, order_id: 1
- cancel_order: order_id: 1, phone: 0612345678

EXAMPLE CORRECT FLOW:
Question: I want to order a margherita pizza and a coke. My name is John, phone 0612345678
Thought: First I need to create an order for this customer
Action: create_order
Action Input: name: John, phone: 0612345678, type: takeaway
Observation: Order #1 created for John (Phone: 0612345678)...
Thought: Order created with ID 1. Now I'll add the items the customer requested.
Action: add_item
Action Input: order_id: 1, item: margherita pizza, quantity: 1, requests: 
Observation: Added 1x Pizza Margherita to order. Current total: €10.50
Thought: Pizza added. Now adding the coke.
Action: add_item
Action Input: order_id: 1, item: coke, quantity: 1, requests: 
Observation: Added 1x Coca-Cola to order. Current total: €13.00
Thought: Both items added. I should show the customer their complete order.
Action: view_order
Action Input: order_id: 1
Observation: Order #1 for John... 1x Pizza Margherita - €10.50, 1x Coca-Cola - €2.50, Total: €13.00
Thought: Order is complete. I'll ask if they want to finalize or add more.
Final Answer: Perfect! I've added 1 Margherita Pizza and 1 Coke to your order. Your current total is €13.00. Would you like to add anything else, or shall I finalize your order?

IMPORTANT REMINDERS:
- ALWAYS create_order before adding items
- ALWAYS remember the order_id from create_order
- ALWAYS wait for Observation before next action
- When customer says items, add them one by one
- When customer is done, use finalize_order
- Be conversational and helpful in Final Answer

Question: {input}
{agent_scratchpad}"""

        prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
            template=template
        )
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15
        )
    
    def process(self, user_input: str) -> str:
        """Process order handling request."""
        try:
            result = self.agent.invoke({
                "input": user_input
            })
            return result['output']
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Could you please rephrase your request?"


# Fonction wrapper pour l'orchestrateur
def order_handling_agent(user_input: str) -> str:
    agent = OrderHandlingAgent()
    return agent.process(user_input)