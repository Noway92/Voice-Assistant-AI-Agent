import os
from datetime import datetime
from langchain_ollama import OllamaLLM
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_react_agent, Tool,AgentExecutor
from langchain_core.prompts import PromptTemplate
from .tools.reservation_tools import (
    check_availability_tool,
    make_reservation_tool,
    cancel_reservation_tool,
    view_reservations_tool
)



class TableReservationAgent:
    def __init__(self,isOffline=True):
        if isOffline:
            self.llm = OllamaLLM(model="llama3", temperature=0)
        else:
            api_key = os.getenv("API_KEY_OPENAI")  # Read key from environment variables
            if not api_key:
                raise ValueError("API_KEY_OPENAI not found in environment variables")
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
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
        template = """You are a helpful restaurant receptionist for table reservations.
Today's date: {today_date}

Available tools:
{tools}

Tool names: {tool_names}

Format to follow:
Question: [customer's request]
Thought: [what to do]
Action: [tool name]
Action Input: [parameters]
Observation: [tool result]
... (repeat Thought/Action/Observation as needed)
Thought: [final reasoning]
Final Answer: [response to customer]

Rules:
1. Always check original Question for name and phone patterns before asking customer
2. To make a reservation: first check_availability, then if available AND you have name+phone, call make_reservation
3. If name or phone is missing after checking the Question, ask for it in Final Answer (don't call make_reservation)
4. Wait for Observation after each Action before continuing
5. Never use placeholders like [Name] or [Phone] in Action Input

Action Input format (no quotes):
- check_availability: date: YYYY-MM-DD, time: HH:MM, guests: NUMBER
- make_reservation: date: YYYY-MM-DD, time: HH:MM, name: FULL_NAME, phone: PHONE, guests: NUMBER, requests: SPECIAL_REQUESTS
- cancel_reservation: date: YYYY-MM-DD, time: HH:MM, name: FULL_NAME
- view_reservations: date: YYYY-MM-DD  OR  all

Example - Making reservation:
Question: I want to book for 4 people tomorrow at 7pm. My name is John Smith, phone 0612345678
Thought: Customer wants reservation. I have name (John Smith) and phone (0612345678). First check availability.
Action: check_availability
Action Input: date: 2025-11-22, time: 19:00, guests: 4
Observation: Tables available for 4 guests on 2025-11-22 at 19:00
Thought: Available. I have name and phone, so I can make the reservation.
Action: make_reservation
Action Input: date: 2025-11-22, time: 19:00, name: John Smith, phone: 0612345678, guests: 4, requests:
Observation: Reservation confirmed for John Smith on 2025-11-22 at 19:00 for 4 guests
Thought: Reservation complete.
Final Answer: Your table for 4 people is confirmed for tomorrow at 7:00 PM under John Smith (0612345678).

Question: {input}
{agent_scratchpad}"""

        prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names","today-date"],
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
        max_iterations=15,  # Increased to allow more complex multi-step reservations
    )

    def process(self, user_input: str) -> str:
        """Process table reservation request."""
        try:
            today_date = datetime.now().strftime("%Y-%m-%d")
            result = self.agent.invoke({
                "input": user_input,
                "today_date": today_date
            })
            return result['output']
        except KeyError as e:
            # Handle missing output key
            return "I apologize, but I couldn't process your reservation request. Could you please rephrase your request with the date, time, and number of guests?"
        except ValueError as e:
            # Handle parsing errors (dates, times, numbers)
            return f"I had trouble understanding the details. Please provide the date (YYYY-MM-DD), time (HH:MM), and number of guests clearly."
        except Exception as e:
            # Generic fallback
            error_msg = str(e).lower()
            if "parsing" in error_msg or "format" in error_msg:
                return "I had trouble understanding your request. Could you please provide: date, time, number of guests, and your contact information?"
            return f"I apologize, I encountered an error: {str(e)}. Could you please rephrase your request?"
        



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