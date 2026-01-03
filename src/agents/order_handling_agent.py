import os
from datetime import datetime
from langchain_ollama import OllamaLLM
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_react_agent, Tool, AgentExecutor
from langchain_core.prompts import PromptTemplate
from .tools.order_tools import (
    create_order_tool,
    add_item_tool,
    update_item_tool,
    remove_item_tool,
    view_order_tool,
    finalize_order_tool,
    check_status_tool,
    cancel_order_tool
)
from .tools.general_inquiry_tools import search_menu_items_tool


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
            ),
            Tool(
                name="search_menu_items",
                func=lambda input_str: self._parse_and_search_menu(input_str),
                description=(
                    "Search for menu items available at the restaurant. "
                    "Input should be: 'query: SEARCH_QUERY' "
                    "SEARCH_QUERY can be: pizza, vegetarian, desserts, chicken, etc. "
                    "Example: 'query: vegetarian dishes' or 'query: pizza'"
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
    
    def _parse_and_search_menu(self, input_str: str) -> str:
        """Parse input and search menu items."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            query = params.get('query', 'menu items')
            return search_menu_items_tool(query)
        except Exception as e:
            return f"Error searching menu: {str(e)}. Please provide: query (what to search for)."
    
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
        template = """You are a restaurant order assistant handling phone orders.

TOOLS AVAILABLE:
{tools}

Tool Names: {tool_names}

STRICT FORMAT (follow exactly):

Question: [customer question]
Thought: [what you need to do]
Action: [exact tool name]
Action Input: [key: value, key: value]
Observation: [tool response]
... (repeat Thought/Action/Input/Observation as needed)
Final Answer: [response to customer]

CRITICAL RULES:
1. NEVER write text without prefix (Thought:/Action:/Action Input:/Final Answer:)
2. After Observation, ALWAYS write "Thought:" before continuing
3. Action Input is REQUIRED - never leave empty
4. Use "Final Answer:" when done (not "I found..." or plain text)

WRONG ❌:
I need to add items
Please provide the items

CORRECT ✅:
Thought: I need to add items
Final Answer: Please provide the items you'd like to order

WORKFLOWS:

NEW ORDER: If has name+phone → create_order → ask what items → add_item → finalize_order
If missing info → ask in Final Answer first (don't call tools)

CHECK STATUS: check_order_status with phone

Tool Input Formats:
- create_order: name: VALUE, phone: VALUE, type: takeaway
- add_item: order_id: VALUE, item: VALUE, quantity: VALUE
- view_order: order_id: VALUE
- finalize_order: order_id: VALUE
- check_order_status: phone: VALUE
- search_menu_items: query: VALUE

EXAMPLE:
Question: I want to order, I'm John, 0612345678
Thought: I have name and phone, I'll create the order
Action: create_order
Action Input: name: John, phone: 0612345678, type: takeaway
Observation: Order #5 created for John
Thought: Order created. I need to ask what items they want
Final Answer: Perfect! Order #5 created. What would you like to order?

Begin! Remember: Every line needs Thought:/Action:/Action Input:/Final Answer:

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
            max_iterations=10
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