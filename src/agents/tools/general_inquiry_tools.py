"""
Tools for querying general restaurant information using RAG (ChromaDB).
"""

import sys
from pathlib import Path

# Add parent directory to path to import rag module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import List, Dict, Any, Optional
from rag.rag import EmbeddingsManager


class GeneralInquiryTools:
    """Tools for querying general restaurant information using RAG."""

    _manager = None

    @classmethod
    def _get_manager(cls) -> EmbeddingsManager:
        """Get or create the embeddings manager singleton."""
        if cls._manager is None:
            try:
                cls._manager = EmbeddingsManager(
                    json_path=str(Path(__file__).parent.parent.parent / "rag" / "general-inqueries.json"),
                    collection_name="restaurant_knowledge"
                )
            except Exception as e:
                raise ConnectionError(f"Failed to initialize EmbeddingsManager: {e}")
        return cls._manager

    @staticmethod
    def search_general_info(query: str, n_results: int = 3) -> str:
        """
        Search for general restaurant information.

        Args:
            query: The user's question
            n_results: Number of results to return (default: 3)

        Returns:
            String with formatted search results
        """
        try:
            manager = GeneralInquiryTools._get_manager()
            results = manager.search(query, n_results=n_results)

            if not results or len(results) == 0:
                return "No relevant information found."

            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                text = result['text']
                metadata = result['metadata']
                score = result.get('score', 0)

                # Only include results with reasonable similarity
                if score > 0.5:  # Threshold for relevance
                    doc_type = metadata.get('type', 'unknown')
                    formatted_results.append(f"[Result {i} - {doc_type}]\n{text}")

            if not formatted_results:
                return "No sufficiently relevant information found."

            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"Error searching information: {str(e)}"

    @staticmethod
    def search_faqs(query: str, n_results: int = 3) -> str:
        """
        Search specifically in FAQs.

        Args:
            query: The user's question
            n_results: Number of results to return

        Returns:
            String with FAQ results
        """
        try:
            manager = GeneralInquiryTools._get_manager()
            results = manager.search(query, n_results=n_results, filter_type="faq")

            if not results or len(results) == 0:
                return "No relevant FAQs found."

            formatted_faqs = []
            for result in results:
                if result.get('score', 0) > 0.5:
                    formatted_faqs.append(result['text'])

            if not formatted_faqs:
                return "No relevant FAQs found."

            return "\n\n".join(formatted_faqs)

        except Exception as e:
            return f"Error searching FAQs: {str(e)}"

    @staticmethod
    def search_location_info(query: str = "location") -> str:
        """
        Get restaurant location information.

        Returns:
            String with location details
        """
        try:
            manager = GeneralInquiryTools._get_manager()
            results = manager.search(query, n_results=1, filter_type="location")

            if results and len(results) > 0:
                return results[0]['text']
            return "Location information not available."

        except Exception as e:
            return f"Error retrieving location: {str(e)}"

    @staticmethod
    def search_opening_hours(query: str = "opening hours") -> str:
        """
        Get restaurant opening hours.

        Returns:
            String with opening hours
        """
        try:
            manager = GeneralInquiryTools._get_manager()
            results = manager.search(query, n_results=1, filter_type="opening_hours")

            if results and len(results) > 0:
                return results[0]['text']
            return "Opening hours information not available."

        except Exception as e:
            return f"Error retrieving opening hours: {str(e)}"

    @staticmethod
    def search_contact_info(query: str = "contact") -> str:
        """
        Get restaurant contact information.

        Returns:
            String with contact details
        """
        try:
            manager = GeneralInquiryTools._get_manager()
            results = manager.search(query, n_results=1, filter_type="contact")

            if results and len(results) > 0:
                return results[0]['text']
            return "Contact information not available."

        except Exception as e:
            return f"Error retrieving contact info: {str(e)}"

    @staticmethod
    def search_special_offers(query: str = "special offers") -> str:
        """
        Get current special offers and promotions.

        Returns:
            String with special offers
        """
        try:
            manager = GeneralInquiryTools._get_manager()
            results = manager.search(query, n_results=5, filter_type="special_offer")

            if not results or len(results) == 0:
                return "No special offers available at the moment."

            offers = []
            for result in results:
                offers.append(result['text'])

            return "\n\n".join(offers)

        except Exception as e:
            return f"Error retrieving special offers: {str(e)}"

    @staticmethod
    def search_dietary_info(query: str) -> str:
        """
        Search for dietary restrictions and allergen information.

        Args:
            query: Query about dietary restrictions or allergens

        Returns:
            String with dietary information
        """
        try:
            manager = GeneralInquiryTools._get_manager()

            # Search in both dietary and allergies types
            results_dietary = manager.search(query, n_results=2, filter_type="dietary")
            results_allergies = manager.search(query, n_results=2, filter_type="allergies")

            all_results = []

            if results_dietary:
                for result in results_dietary:
                    if result.get('score', 0) > 0.5:
                        all_results.append(result['text'])

            if results_allergies:
                for result in results_allergies:
                    if result.get('score', 0) > 0.5:
                        all_results.append(result['text'])

            if not all_results:
                return "No specific dietary information found. Please contact the restaurant for detailed allergen information."

            return "\n\n".join(all_results)

        except Exception as e:
            return f"Error retrieving dietary information: {str(e)}"

    @staticmethod
    def search_menu_items(query: str, n_results: int = 5) -> str:
        """
        Search for menu items from the database.

        Args:
            query: Search query about menu dishes (e.g., "vegetarian dishes", "desserts", "chicken")
            n_results: Number of results to return (default: 5)

        Returns:
            String with formatted menu items
        """
        try:
            manager = GeneralInquiryTools._get_manager()
            results = manager.search(query, n_results=n_results, filter_type="menu_item")

            if not results or len(results) == 0:
                return "No menu items found matching your query."

            formatted_items = []
            for i, result in enumerate(results, 1):
                if result.get('score', 0) > 0.5:
                    text = result['text']
                    metadata = result['metadata']
                    
                    # Extract key information from metadata
                    name = metadata.get('name', 'Unknown')
                    category = metadata.get('category', 'N/A')
                    price = metadata.get('price', 'N/A')
                    available = metadata.get('is_available', True)
                    
                    # Format the item
                    availability = "Available" if available else "Not Available"
                    formatted_items.append(
                        f"{i}. {name} ({category}) - ${price}\n"
                        f"   {availability}\n"
                        f"   {text}"
                    )

            if not formatted_items:
                return "No relevant menu items found."

            return "\n\n".join(formatted_items)

        except Exception as e:
            return f"Error searching menu items: {str(e)}"


# Tool functions for LangChain/agent integration
def search_general_info_tool(query: str) -> str:
    """Search for general restaurant information."""
    return GeneralInquiryTools.search_general_info(query)


def search_faqs_tool(query: str) -> str:
    """Search in FAQs."""
    return GeneralInquiryTools.search_faqs(query)


def search_location_tool() -> str:
    """Get location information."""
    return GeneralInquiryTools.search_location_info()


def search_opening_hours_tool() -> str:
    """Get opening hours."""
    return GeneralInquiryTools.search_opening_hours()


def search_contact_tool() -> str:
    """Get contact information."""
    return GeneralInquiryTools.search_contact_info()


def search_special_offers_tool() -> str:
    """Get special offers."""
    return GeneralInquiryTools.search_special_offers()


def search_dietary_tool(query: str) -> str:
    """Search dietary and allergen information."""
    return GeneralInquiryTools.search_dietary_info(query)


def search_menu_items_tool(query: str) -> str:
    """Search for menu items from the database."""
    return GeneralInquiryTools.search_menu_items(query, n_results=10)

