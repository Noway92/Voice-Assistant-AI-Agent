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
    search_dietary_tool,
    search_menu_items_tool
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
            ),
            Tool(
                name="search_menu",
                func=search_menu_items_tool,
                description=(
                    "Search for menu items and dishes from the restaurant database. "
                    "Use this when asked about specific dishes, menu categories, "
                    "what food is available, dish recommendations, prices, or ingredients. "
                    "Examples: 'What vegetarian dishes do you have?', 'Show me desserts', "
                    "'Do you have pasta?', 'What's on the menu?'. "
                    "Input: the user's question about menu items as a string."
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

Question: [customer's request]
Thought: [what to do]
Action: [tool name]
Action Input: [parameters]
Observation: [tool result]
... (repeat Thought/Action/Observation as needed)
Thought: [final reasoning]
Final Answer: [friendly response to the customer based on the information retrieved]

MANDATORY RULES:

1. ALWAYS start your final response with "Final Answer:" (not "I found" or anything else)
2. NEVER write text without a prefix (Thought:/Action:/Action Input:/Observation:/Final Answer:)

IMPORTANT GUIDELINES:

1. Always use the most specific tool available for the question
2. If asked about location/address → use get_location
3. If asked about hours/schedule → use get_opening_hours
4. If asked about contact info → use get_contact
5. If asked about offers/promotions → use get_special_offers
6. If asked about dietary/allergies → use search_dietary_info
7. If asked about menu items/dishes/food → use search_menu
8. If it seems like a common question → try search_faqs first
9. For other general questions → use search_general_info
10. ALWAYS retrieve information using tools before answering
11. Base your Final Answer ONLY on the information from the Observation
12. If the Observation says "No relevant information found", be honest and suggest contacting the restaurant
13. Be conversational, friendly, and professional in your Final Answer
14. NEVER skip the "Thought:" after Observation
15. If no tool has good information, STILL write "Final Answer:" and be honest

EXAMPLE - When tool finds nothing:
Question: Do you have any moon pizza?
Thought: This is about menu items, I should search the menu.
Action: search_menu
Action Input: moon pizza
Observation: No menu items found matching your query.
Thought: The tool found nothing. I should tell the customer honestly.
Final Answer: I couldn't find a moon pizza on our menu. Would you like to check our other pizzas? Please feel free to call us for more options.

EXAMPLE - When tool finds something:
Question: What vegetarian dishes do you have?
Thought: This is about menu items, I should search for vegetarian dishes.
Action: search_menu
Action Input: vegetarian dishes
Observation: 1. Vegetable Stir Fry - $12.99, 2. Tofu Curry - $14.99
Thought: Great! I have menu items. I can answer now.
Final Answer: We have several vegetarian options including Vegetable Stir Fry ($12.99) and Tofu Curry ($14.99). Would you like more details?

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