from langchain_ollama import OllamaLLM
from langchain.agents import create_react_agent, Tool,AgentExecutor
from langchain_core.prompts import PromptTemplate
from .tools.reservation_tools import (
    check_availability_tool,
    make_reservation_tool,
    cancel_reservation_tool,
    view_reservations_tool
)


class TableReservationAgent:
    def __init__(self, model_name="llama3"):
        self.llm = OllamaLLM(model=model_name, temperature=0)
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self):
        """Create tools for the agent."""
        return [
            Tool(
                name="check_availability",
                func=lambda input_str: self._parse_and_check_availability(input_str),
                description=(
                    "Check table availability. "
                    "Input should be: 'date: YYYY-MM-DD, time: HH:MM, guests: NUMBER'. "
                    "Example: 'date: 2025-11-20, time: 19:00, guests: 4'"
                )
            ),
            Tool(
                name="make_reservation",
                func=lambda input_str: self._parse_and_make_reservation(input_str),
                description=(
                    "Make a table reservation. "
                    "Input should be: 'date: YYYY-MM-DD, time: HH:MM, name: NAME, "
                    "phone: PHONE, guests: NUMBER, requests: REQUESTS'. "
                    "Example: 'date: 2025-11-20, time: 19:00, name: Jean Dupont, "
                    "phone: 0612345678, guests: 4, requests: Fenêtre'"
                )
            ),
            Tool(
                name="cancel_reservation",
                func=lambda input_str: self._parse_and_cancel_reservation(input_str),
                description=(
                    "Cancel a reservation. "
                    "Input should be: 'date: YYYY-MM-DD, time: HH:MM, name: NAME'. "
                    "Example: 'date: 2025-11-20, time: 19:00, name: Jean Dupont'"
                )
            ),
            Tool(
                name="view_reservations",
                func=lambda input_str: self._parse_and_view_reservations(input_str),
                description=(
                    "View all reservations. "
                    "Input should be: 'date: YYYY-MM-DD' or 'all' to view all reservations. "
                    "Example: 'date: 2025-11-20' or 'all'"
                )
            )
        ]
    
    def _parse_and_check_availability(self, input_str: str) -> str:
        """Parse input and check availability."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return check_availability_tool(
                params['date'],
                params['time'],
                int(params['guests'])
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: date, time, and guests."
    
    def _parse_and_make_reservation(self, input_str: str) -> str:
        """Parse input and make reservation."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return make_reservation_tool(
                params['date'],
                params['time'],
                params['name'],
                params['phone'],
                int(params['guests']),
                params.get('requests', '')
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: date, time, name, phone, and guests."
    
    def _parse_and_cancel_reservation(self, input_str: str) -> str:
        """Parse input and cancel reservation."""
        try:
            input_str = input_str.strip().strip("'\"")
            params = self._parse_input(input_str)
            return cancel_reservation_tool(
                params['date'],
                params['time'],
                params['name']
            )
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: date, time, and name."
    
    def _parse_and_view_reservations(self, input_str: str) -> str:
        """Parse input and view reservations."""
        try:
            input_str = input_str.strip().strip("'\"").lower()
            if input_str == 'all':
                return view_reservations_tool()
            params = self._parse_input(input_str)
            return view_reservations_tool(params.get('date'))
        except Exception as e:
            return f"Error parsing input: {str(e)}. Please provide: 'all' or 'date: YYYY-MM-DD'."
    
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
        """Create the ReAct agent."""
        template = """You are a helpful restaurant receptionist assistant for table reservations.

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

        STRICT RULES - READ CAREFULLY:
        1. You can call check_availability ONLY ONCE per conversation
        2. You can call make_reservation ONLY ONCE per conversation
        3. You can call cancel_reservation ONLY ONCE per conversation
        4. You can call view_reservations ONLY ONCE per conversation
        5. After ANY Action, you MUST either:
        - Call a DIFFERENT tool, OR
        - Go directly to Final Answer
        6. If you already called a tool, DO NOT call it again - use the previous result

        WORKFLOWS:

        A) Customer wants to MAKE a reservation:
        Step 1: check_availability (once) with date, time, guests
        Step 2: Check if you have BOTH name AND phone from the customer
        Step 3a: If name OR phone is MISSING → Final Answer asking for the missing information
        Step 3b: If you have BOTH name AND phone → make_reservation (once) → Final Answer confirming
        
        CRITICAL: DO NOT call make_reservation if:
        - Customer has not provided their name
        - Customer has not provided their phone number
        - You are using placeholders like [Customer's Name] or [Customer's Phone Number]
        
        If information is missing, ask in Final Answer: "Great! Tables are available. May I have your name and phone number to complete the reservation?"

        B) Customer wants to CHECK availability only:
        Step 1: check_availability (once) → Final Answer with results

        C) Customer wants to CANCEL a reservation:
        Step 1: If you don't have name, date, or time → Final Answer asking for it
        Step 2: If you have all info → cancel_reservation (once) → Final Answer confirming

        D) Customer wants to VIEW reservations:
        Step 1: view_reservations (once) with date or 'all' → Final Answer with list

        Action Input format (NO quotes, NO placeholders):
        - check_availability: date: 2025-11-20, time: 19:00, guests: 4
        - make_reservation: date: 2025-11-20, time: 19:00, name: Jean Dupont, phone: 0612345678, guests: 4, requests: 
        - cancel_reservation: date: 2025-11-20, time: 19:00, name: Jean Dupont
        - view_reservations: date: 2025-11-20 OR all

        REMEMBER: 
        - Each tool can be called ONLY ONCE
        - NEVER use placeholders like [Name] or [Phone]
        - If customer info is missing, ask for it in Final Answer BEFORE calling make_reservation

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
        max_iterations=4,  # Réduit à 4 pour forcer l'arrêt
    )
    
    def process(self, user_input: str) -> str:
        """Process table reservation request."""
        try:
            result = self.agent.invoke({"input": user_input})
            return result['output']
        except Exception as e:
            return f"Désolé, j'ai rencontré une erreur : {str(e)}. Pouvez-vous reformuler votre demande ?"
        



"""
Ancien Prompt : 

template =You are a helpful restaurant receptionist assistant for table reservations.
Your job is to help customers make, check, or cancel table reservations in a friendly and professional manner.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

Always follow this format:

Question: the customer's request
Thought: think about what you need to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final response to the customer in a friendly, conversational way

IMPORTANT INSTRUCTIONS:
1. When a customer asks for a reservation, ALWAYS first check availability before making the reservation
2. Extract all necessary information from the customer (date, time, number of guests, name, phone)
3. If information is missing, ask the customer politely
4. When confirming a reservation, repeat all details back to the customer
5. Be conversational and friendly in your Final Answer
6. Use dates in YYYY-MM-DD format and times in HH:MM format (24-hour)
7. Always respond in the same language as the customer (French or English)

Current conversation:
Question: {input}
{agent_scratchpad}
"""