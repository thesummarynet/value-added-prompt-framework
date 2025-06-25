#!/usr/bin/env python3
"""
OpenAI Utility Functions with Structured Outputs

This module provides utility functions for interacting with the OpenAI API,
including text generation, image generation, and structured JSON responses.
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
from pydantic import BaseModel

# Global client variable
client = None

def get_client(api_key: Optional[str] = None):
    """
    Get or initialize the OpenAI client.
    
    Args:
        api_key: Optional API key to use (overrides environment variable)
    
    Returns:
        OpenAI client instance
    
    Raises:
        ValueError: If API key is not set
    """
    global client
    
    # Use provided API key, fall back to environment variable
    key_to_use = api_key or os.getenv("OPENAI_API_KEY")
    
    if not key_to_use:
        raise ValueError("OpenAI API key not provided. Please provide it via parameter or set OPENAI_API_KEY environment variable.")
    
    # Reinitialize client if we have a new API key
    if client is None or (api_key and api_key != getattr(client, '_api_key', None)):
        client = OpenAI(api_key=key_to_use)
        # Store the key for comparison (not the full key for security)
        client._api_key = key_to_use[:8] + "..." if key_to_use else None
    
    return client


async def generate_text(model: str, messages: List[Dict[str, Any]], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate text using OpenAI models.
    
    Args:
        model: The model to use (e.g., 'gpt-4o-mini', 'gpt-3.5-turbo')
        messages: List of message objects in the format [{"role": "...", "content": "..."}]
        api_key: Optional API key to use
        
    Returns:
        Dict containing generated text and usage information
    
    Raises:
        ValueError: If no messages are provided
        Exception: Any errors from the OpenAI API
    """
    try:
        if not messages:
            raise ValueError("No messages provided.")
        
        # Get client with optional API key
        openai_client = get_client(api_key)
        
        completion = openai_client.chat.completions.create(
            model=model,
            messages=messages
        )
        
        return {
            "text": completion.choices[0].message.content,
            "usage": completion.usage.total_tokens if completion.usage else 0,
            "input_tokens": completion.usage.prompt_tokens if completion.usage else 0,
            "output_tokens": completion.usage.completion_tokens if completion.usage else 0,
        }
    except Exception as error:
        print(f"Error generating text: {error}")
        raise


class PsychologistResponse(BaseModel):
    """Structured response model for psychologist interactions."""
    response: str
    psychiatrist_thoughts: str


async def generate_structured_response(
    model: str, 
    messages: List[Dict[str, Any]], 
    response_model: BaseModel = PsychologistResponse,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a structured JSON response using OpenAI's structured outputs.
    
    Args:
        model: The model to use (must support structured outputs)
        messages: List of message objects
        response_model: Pydantic model for the expected response structure
        api_key: Optional API key to use
        
    Returns:
        Dict containing the structured response and usage information
    
    Raises:
        ValueError: If no messages are provided or response parsing fails
        Exception: Any errors from the OpenAI API
    """
    try:
        if not messages:
            raise ValueError("No messages provided.")
        
        # Get client with optional API key
        openai_client = get_client(api_key)
        
        # Use structured outputs with the response format
        completion = openai_client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=response_model
        )
        
        # Check for refusal
        if completion.choices[0].message.refusal:
            raise ValueError(f"Model refused to respond: {completion.choices[0].message.refusal}")
        
        parsed_response = completion.choices[0].message.parsed
        
        return {
            "structured_output": parsed_response.dict(),
            "usage": completion.usage.total_tokens if completion.usage else 0,
            "input_tokens": completion.usage.prompt_tokens if completion.usage else 0,
            "output_tokens": completion.usage.completion_tokens if completion.usage else 0,
        }
    except Exception as error:
        print(f"Error generating structured response: {error}")
        raise


def parse_json(content: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Safely parse a JSON string.
    
    Args:
        content: JSON string to parse
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    if content is None:
        return None
    
    try:
        return json.loads(content)
    except Exception:
        return None


async def generate_json_custom_ai(
    message: str, 
    prompt_id: int, 
    system_prompts: List[Dict[str, Any]], 
    retry_count: int = 0,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a JSON response from a custom AI.
    
    Args:
        message: User message
        prompt_id: ID of the system prompt to use
        system_prompts: List of system prompts
        retry_count: Number of retries attempted (default: 0)
        api_key: Optional API key to use
        
    Returns:
        Dict containing the parsed JSON output and token usage
    
    Raises:
        ValueError: If system prompt not found or JSON parsing fails after retries
        Exception: Any errors from the OpenAI API
    """
    try:
        # Find the system prompt with the specified ID
        system_prompt = next((p for p in system_prompts if p.get("id") == prompt_id), None)
        
        if not system_prompt:
            raise ValueError(f"System prompt with ID {prompt_id} not found")
        
        system_message = system_prompt.get("message", "")
        model = system_prompt.get("model", "gpt-4o-mini")
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
        
        response = await generate_text(model, messages, api_key)
        
        # Clean and parse the response
        if response.get("text"):
            cleaned_response = response["text"].replace("```json", "").replace("```", "")
            parsed_response = parse_json(cleaned_response)
            
            if not parsed_response and retry_count < 5:
                print(f"Retrying OpenAI query, retry count: {retry_count + 1}")
                return await generate_json_custom_ai(message, prompt_id, system_prompts, retry_count + 1, api_key)
            elif not parsed_response:
                raise ValueError("Exceeded retry attempts for getting JSON response from OpenAI")
            
            return {
                "output": parsed_response,
                "promptTokens": response.get("input_tokens"),
                "completionTokens": response.get("output_tokens"),
                "usage": response.get("usage"),
                "model": model
            }
        else:
            raise ValueError("No text in response")
    except Exception as error:
        print(f"Error generating custom AI response: {error}")
        raise


async def add_messages(
    messages: List[Dict[str, Any]], 
    new_messages: Union[List[Dict[str, Any]], Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Add new messages to an existing messages array.
    
    Args:
        messages: Existing chat messages
        new_messages: New message or list of messages to add
        
    Returns:
        Updated list of messages
    """
    if isinstance(new_messages, dict):
        return messages + [new_messages]
    elif isinstance(new_messages, list):
        return messages + new_messages
    else:
        raise TypeError("new_messages must be a dict or a list of dicts")