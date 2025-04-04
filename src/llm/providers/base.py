import abc
from typing import List, Dict, Tuple, Optional, Union, Callable, Any

class LLMProviderInterface(abc.ABC):
    """
    Abstract Base Class for LLM Provider implementations.
    Defines the common interface for interacting with different LLM APIs.
    """

    def __init__(self, api_key: Optional[str], api_url: str, model: str, **kwargs):
        """
        Initializes the provider.

        Args:
            api_key: The API key for the service (can be None for some providers like Ollama).
            api_url: The base URL for the API endpoint.
            model: The specific model name to use.
            **kwargs: Additional provider-specific configuration (e.g., temperature, max_tokens).
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.config_kwargs = kwargs # Store extra config like temperature, max_tokens, timeout

    @abc.abstractmethod
    def get_identifier(self) -> str:
        """Returns a unique string identifier for this provider (e.g., 'openai', 'ollama')."""
        pass

    @abc.abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Returns the necessary HTTP headers for API requests."""
        pass

    @abc.abstractmethod
    def prepare_request_payload(self, messages: List[Dict[str, str]], stream: bool, **kwargs) -> Dict[str, Any]:
        """
        Prepares the JSON payload for the API request.

        Args:
            messages: The list of messages for the conversation.
            stream: Boolean indicating if the request is for streaming.
            **kwargs: Additional parameters specific to the request type (e.g., analysis vs chat).

        Returns:
            A dictionary representing the JSON payload.
        """
        pass

    @abc.abstractmethod
    def parse_response(self, response_data: Dict[str, Any]) -> str:
        """
        Parses the content from a non-streaming API response.

        Args:
            response_data: The JSON dictionary returned by the API.

        Returns:
            The extracted text content. Returns an empty string if parsing fails or content is empty.
        """
        pass

    @abc.abstractmethod
    def parse_stream_chunk(self, chunk_data: Union[str, bytes]) -> Optional[str]:
        """
        Parses a single chunk from a streaming API response.

        Args:
            chunk_data: The raw chunk data (string or bytes) received from the stream.

        Returns:
            The extracted text content from the chunk, or None if it's not a content chunk
            or if parsing fails.
        """
        pass

    @abc.abstractmethod
    def get_stream_stop_signal(self) -> Optional[str]:
        """
        Returns the specific signal string or pattern that indicates the end of a stream
        for this provider (e.g., '[DONE]'). Returns None if not applicable.
        """
        pass

    @abc.abstractmethod
    def test_connection_payload(self) -> Dict[str, Any]:
        """
        Returns a minimal JSON payload suitable for testing the API connection.
        """
        pass

    @abc.abstractmethod
    def check_test_connection_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Checks if the response from a test connection request indicates success.

        Args:
            response_data: The JSON dictionary returned by the test API call.

        Returns:
            True if the connection seems successful based on the response structure, False otherwise.
        """
        pass

    # --- Helper methods that might be common but can be overridden ---

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Safely retrieves a value from the stored configuration kwargs."""
        return self.config_kwargs.get(key, default)