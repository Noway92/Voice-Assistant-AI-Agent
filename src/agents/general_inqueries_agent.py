import os
from langchain_ollama import OllamaLLM
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_react_agent, Tool, AgentExecutor
from langchain_core.prompts import PromptTemplate
from .tools.general_inquiry_tools import (
    search_general_info_tool,
    search_faqs_tool,
    search_location_tool,
    search_opening_hours_tool,
    search_contact_tool,
    search_special_offers_tool,
    search_dietary_tool
)


class GeneralInqueriesAgent:
    """Agent for handling general inquiries about the restaurant using RAG."""

    def __init__(self, isOffline=True):
        """Initialize the agent with LLM and RAG tools."""
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
        """Create RAG-based tools for the agent."""
        return [
            Tool(
                name="search_general_info",
                func=search_general_info_tool,
                description=(
                    "Search for general information about the restaurant. "
                    "Use this for questions about restaurant policies, atmosphere, "
                    "accessibility, parking, payment methods, delivery, or any general topic. "
                    "Input: the user's question as a string."
                )
            ),
            Tool(
                name="search_faqs",
                func=search_faqs_tool,
                description=(
                    "Search in frequently asked questions (FAQs). "
                    "Use this when the user's question seems like a common question "
                    "(e.g., pets policy, children's menu, private events, terrace). "
                    "Input: the user's question as a string."
                )
            ),
            Tool(
                name="get_location",
                func=lambda _: search_location_tool(),
                description=(
                    "Get the restaurant's location, address, and directions. "
                    "Use this when asked about 'where', 'address', 'location', 'directions', or 'how to get there'. "
                    "Input: empty string or any text (ignored)."
                )
            ),
            Tool(
                name="get_opening_hours",
                func=lambda _: search_opening_hours_tool(),
                description=(
                    "Get the restaurant's opening hours and schedule. "
                    "Use this when asked about 'hours', 'schedule', 'open', 'close', or 'when'. "
                    "Input: empty string or any text (ignored)."
                )
            ),
            Tool(
                name="get_contact",
                func=lambda _: search_contact_tool(),
                description=(
                    "Get the restaurant's contact information (phone, email, website, social media). "
                    "Use this when asked about 'contact', 'phone', 'email', 'website', or 'social media'. "
                    "Input: empty string or any text (ignored)."
                )
            ),
            Tool(
                name="get_special_offers",
                func=lambda _: search_special_offers_tool(),
                description=(
                    "Get current special offers, promotions, and deals. "
                    "Use this when asked about 'offers', 'promotions', 'deals', 'discounts', "
                    "'happy hour', or 'lunch menu'. "
                    "Input: empty string or any text (ignored)."
                )
            ),
            Tool(
                name="search_dietary_info",
                func=search_dietary_tool,
                description=(
                    "Search for dietary restrictions and allergen information. "
                    "Use this when asked about allergies, dietary options, vegetarian, "
                    "vegan, gluten-free, halal, kosher, or any dietary restrictions. "
                    "Input: the user's question about dietary needs as a string."
                )
            )
        ]

    def _create_agent(self):
        """Create the ReAct agent with RAG tools."""
        template = """You are a helpful and professional restaurant assistant.
Your role is to answer general questions about the restaurant using the available tools.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

Use this EXACT format:

Question: the customer's question
Thought: what information do I need to answer this question?
Action: [tool name]
Action Input: [input for the tool]
Observation: [result from the tool]
Thought: do I have enough information to answer?
Final Answer: [friendly response to the customer based on the information retrieved]

IMPORTANT GUIDELINES:
1. Always use the most specific tool available for the question
2. If asked about location/address → use get_location
3. If asked about hours/schedule → use get_opening_hours
4. If asked about contact info → use get_contact
5. If asked about offers/promotions → use get_special_offers
6. If asked about dietary/allergies → use search_dietary_info
7. If it seems like a common question → try search_faqs first
8. For other general questions → use search_general_info

9. ALWAYS retrieve information using tools before answering
10. Base your Final Answer ONLY on the information from the Observation
11. If the Observation says "No relevant information found", be honest and suggest contacting the restaurant
12. Be conversational, friendly, and professional in your Final Answer
13. Respond in the same language as the customer (French or English)
14. After using a tool and getting an Observation, go directly to Final Answer

EXAMPLE FLOW:
Question: What are your opening hours?
Thought: This is about opening hours, I should use the get_opening_hours tool.
Action: get_opening_hours
Action Input: opening hours
Observation: [hours information from RAG]
Thought: I have the opening hours information.
Final Answer: [Friendly response with the hours]

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
            max_iterations=8
        )

    def process(self, user_input: str) -> str:
        """Process a general inquiry using RAG."""
        try:
            result = self.agent.invoke({"input": user_input})
            return result['output']
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try rephrasing your question."


# Fonction wrapper pour l'orchestrateur
def general_inqueries_agent(user_input: str, isOffline=True) -> str:
    """Wrapper function for the orchestrator."""
    agent = GeneralInqueriesAgent(isOffline=isOffline)
    return agent.process(user_input)