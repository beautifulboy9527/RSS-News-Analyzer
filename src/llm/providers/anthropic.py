import json
import logging
from typing import List, Dict, Optional, Union, Any

from .base import LLMProviderInterface

logger = logging.getLogger('news_analyzer.llm.provider.anthropic')

class AnthropicProvider(LLMProviderInterface):
    """LLM Provider implementation for Anthropic API."""

    def get_identifier(self) -> str:
        return "anthropic"

    def get_headers(self) -> Dict[str, str]:
        """Returns headers for Anthropic API."""
        if not self.api_key:
            raise ValueError(f"API key is required for provider '{self.get_identifier()}'.")
        return {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': self._get_config_value('anthropic_version', '2023-06-01') # Allow overriding version
        }

    def prepare_request_payload(self, messages: List[Dict[str, str]], stream: bool, **kwargs) -> Dict[str, Any]:
        """Prepares the JSON payload for Anthropic API."""
        # Anthropic doesn't use 'system' role directly in messages, it uses a system parameter
        system_prompt = ""
        user_assistant_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content'] # Extract system prompt
            else:
                user_assistant_messages.append(msg)

        payload = {
            'model': self.model,
            'messages': user_assistant_messages,
            'stream': stream
        }
        if system_prompt:
            payload['system'] = system_prompt

        # Add optional parameters
        temperature = self._get_config_value('temperature')
        if temperature is not None:
            payload['temperature'] = temperature

        # Anthropic uses 'max_tokens' directly in the root
        max_tokens = self._get_config_value('max_tokens')
        if max_tokens is not None:
            payload['max_tokens'] = max_tokens # Note: Anthropic calls this max_tokens_to_sample in older versions

        payload.update(kwargs)
        return payload

    def parse_response(self, response_data: Dict[str, Any]) -> str:
        """Parses the content from a non-streaming Anthropic response."""
        try:
            # Content is a list of blocks, usually one text block
            content_blocks = response_data.get('content', [])
            text_content = ""
            for block in content_blocks:
                if block.get('type') == 'text':
                    text_content += block.get('text', '')
            return text_content.strip()
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Failed to extract content from '{self.get_identifier()}' response: {e}. Response: {response_data}", exc_info=True)
            return ""

    def parse_stream_chunk(self, chunk_data: Union[str, bytes]) -> Optional[str]:
        """Parses a single chunk from an Anthropic SSE stream."""
        # Anthropic SSE events: ping, message_start, content_block_start, content_block_delta, content_block_stop, message_delta, message_stop
        # We are interested in 'content_block_delta' with type 'text_delta'
        if isinstance(chunk_data, bytes):
            try:
                decoded_chunk = chunk_data.decode('utf-8').strip()
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode stream chunk as UTF-8: {chunk_data!r}")
                return None
        else:
            decoded_chunk = chunk_data.strip()

        # Anthropic stream sends events line by line, e.g., "event: content_block_delta\ndata: {...}"
        # We assume the caller (e.g., httpx-sse) handles parsing the event and data fields.
        # This method receives the 'data' part of the relevant event.
        if not decoded_chunk:
            return None

        try:
            # We expect the data part of a content_block_delta event here
            data = json.loads(decoded_chunk)
            if data.get('type') == 'content_block_delta':
                 delta = data.get('delta', {})
                 if delta.get('type') == 'text_delta':
                     return delta.get('text', '') # Return the text delta
            # Other event types like message_stop don't contain content delta
            return None
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Error parsing '{self.get_identifier()}' SSE data: {e}. Data: {decoded_chunk}")
            return None

    def get_stream_stop_signal(self) -> Optional[str]:
        """Anthropic stream ends with 'message_stop' event, not a specific data string."""
        # The streaming client should detect the end based on the event type or stream closure.
        return None # No specific data signal like "[DONE]"

    def test_connection_payload(self) -> Dict[str, Any]:
        """Returns a minimal payload for testing Anthropic connections."""
        # Need to handle the system prompt extraction for the test payload as well
        test_messages = [{'role': 'user', 'content': 'Say "Hello"'}]
        payload = {
            'model': self.model,
            'messages': test_messages,
            'max_tokens': 5 # Use max_tokens for consistency with API
        }
        # Add temperature if configured
        temperature = self._get_config_value('temperature')
        if temperature is not None:
             payload['temperature'] = temperature
        return payload


    def check_test_connection_response(self, response_data: Dict[str, Any]) -> bool:
        """Checks if the test connection response for Anthropic API is valid."""
        # A successful response usually contains a 'content' list or at least a 'type' like 'message'
        # and no 'error' block at the top level.
        has_content = 'content' in response_data and isinstance(response_data.get('content'), list)
        has_type = 'type' in response_data
        has_error = 'error' in response_data and response_data.get('error') is not None
        return (has_content or has_type) and not has_error