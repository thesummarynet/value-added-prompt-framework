#!/usr/bin/env python3
"""
Value-Added Prompt Framework

This module implements the Value-Added Prompt Framework for enhanced
LLM interactions with dynamic context injection and temporal awareness.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
import logging

# Import our utility modules
from utils.value_added_utils import (
    SessionTimer, 
    get_default_patient_history, 
    create_enhanced_user_input,
    get_system_prompt,
    create_session_start_message,
    validate_enhanced_input,
    extract_session_metrics
)

from utils.openai_utils import (
    generate_structured_response,
    PsychologistResponse,
    add_messages
)

from utils.chat_utils import (
    begin_chat,
    fetch_chat,
    add_message,
    parse_chat
)


@dataclass
class FrameworkConfig:
    """Configuration for the Value-Added Framework."""
    model: str = "gpt-4o-mini"
    session_duration_minutes: int = 50
    db_name: str = "psychology_sessions"
    max_retries: int = 3
    api_key: Optional[str] = None


class ValueAddedFramework:
    """
    Main class implementing the Value-Added Prompt Framework.
    
    This framework enhances LLM interactions by:
    - Injecting contextual information into prompts
    - Managing session timing and temporal awareness
    - Providing structured responses with clinical insights
    - Maintaining conversation history and patient context
    """
    
    def __init__(self, config: FrameworkConfig = None):
        """
        Initialize the Value-Added Framework.
        
        Args:
            config: Framework configuration (uses defaults if None)
        """
        self.config = config or FrameworkConfig()
        self.timer = SessionTimer(self.config.session_duration_minutes)
        self.patient_history = get_default_patient_history()
        self.current_session = 1
        self.chat_id = None
        self.session_started = False
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def start_session(self) -> str:
        """
        Start a new therapy session.
        
        Returns:
            Chat ID for the new session
        """
        try:
            # Create new chat
            self.chat_id = begin_chat(self.config.db_name)
            
            # Start timer
            self.timer.start_session()
            self.session_started = True
            
            # Add initial system message and session start message
            system_prompt = get_system_prompt()
            add_message(self.config.db_name, self.chat_id, "system", system_prompt)
            
            # Add the session start message
            start_msg = create_session_start_message()
            add_message(self.config.db_name, self.chat_id, "user", start_msg["content"])
            
            self.logger.info(f"Session started with chat ID: {self.chat_id}")
            return self.chat_id
            
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            raise
    
    def update_patient_history(self, new_history: Dict[str, Any]):
        """
        Update patient history.
        
        Args:
            new_history: New patient history data
        """
        self.patient_history = new_history
        self.logger.info("Patient history updated")
    
    def set_current_session(self, session_number: int):
        """
        Set the current session number.
        
        Args:
            session_number: Session number
        """
        self.current_session = session_number
        self.logger.info(f"Current session set to: {session_number}")
    
    async def process_user_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process user message through the Value-Added Framework.
        
        Args:
            user_message: Raw user input
            
        Returns:
            Dict containing the framework response and metadata
        """
        if not self.session_started:
            raise ValueError("Session not started. Call start_session() first.")
        
        try:
            # Create enhanced user input
            enhanced_input = create_enhanced_user_input(
                user_message,
                self.timer,
                self.current_session,
                self.patient_history
            )
            
            # Validate enhanced input
            if not validate_enhanced_input(enhanced_input):
                raise ValueError("Enhanced input validation failed")
            
            # Get chat history
            chat_messages = fetch_chat(self.config.db_name, self.chat_id) or []
            
            # Convert to OpenAI format and add enhanced input
            openai_messages = []
            for msg in chat_messages:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add the enhanced user message
            openai_messages.append({
                "role": "user",
                "content": enhanced_input
            })
            
            # Generate structured response
            response_data = await generate_structured_response(
                model=self.config.model,
                messages=openai_messages,
                response_model=PsychologistResponse,
                api_key=self.config.api_key
            )
            
            # Extract the structured output
            structured_output = response_data["structured_output"]
            
            # Save the original user message and AI response to chat
            add_message(self.config.db_name, self.chat_id, "user", user_message)
            add_message(self.config.db_name, self.chat_id, "assistant", structured_output["response"])
            
            # Get session metrics
            session_metrics = self.extract_session_metrics()
            
            # Prepare response
            framework_response = {
                "patient_response": structured_output["response"],
                "psychiatrist_thoughts": structured_output["psychiatrist_thoughts"],
                "session_metrics": session_metrics,
                "time_left": self.timer.get_time_left_string(),
                "session_active": self.timer.is_session_active(),
                "current_session": self.current_session,
                "usage_stats": {
                    "input_tokens": response_data.get("input_tokens", 0),
                    "output_tokens": response_data.get("output_tokens", 0),
                    "total_tokens": response_data.get("usage", 0)
                }
            }
            
            self.logger.info(f"Processed message successfully. Time left: {self.timer.get_time_left_string()}")
            return framework_response
            
        except Exception as e:
            self.logger.error(f"Error processing user message: {e}")
            raise
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current session.
        
        Returns:
            Dict containing session summary
        """
        chat_messages = fetch_chat(self.config.db_name, self.chat_id) or []
        
        # Filter out system messages and count interactions
        user_messages = [msg for msg in chat_messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in chat_messages if msg["role"] == "assistant"]
        
        return {
            "chat_id": self.chat_id,
            "session_number": self.current_session,
            "session_metrics": self.extract_session_metrics(),
            "message_count": {
                "user": len(user_messages),
                "assistant": len(assistant_messages),
                "total": len(chat_messages)
            },
            "session_duration_minutes": self.config.session_duration_minutes,
            "patient_name": self.patient_history.get("name", "Unknown")
        }
    
    def end_session(self) -> Dict[str, Any]:
        """
        End the current session and return summary.
        
        Returns:
            Final session summary
        """
        summary = self.get_session_summary()
        
        # Add session end message
        if self.chat_id:
            end_message = f"Session {self.current_session} ended. Duration: {self.config.session_duration_minutes} minutes."
            add_message(self.config.db_name, self.chat_id, "system", end_message)
        
        self.session_started = False
        self.logger.info(f"Session {self.current_session} ended")
        
        return summary
    
    def extract_session_metrics(self) -> Dict[str, Any]:
        """
        Extract session metrics for analysis.
        
        Returns:
            Dict containing session metrics
        """
        return extract_session_metrics(self.timer)
    
    def get_chat_history(self, formatted: bool = False) -> List[Dict[str, Any]]:
        """
        Get chat history for the current session.
        
        Args:
            formatted: Whether to return formatted chat string
            
        Returns:
            Chat history
        """
        if not self.chat_id:
            return []
        
        if formatted:
            return parse_chat(
                self.config.db_name, 
                self.chat_id, 
                "Patient", 
                "Therapist"
            )
        
        return fetch_chat(self.config.db_name, self.chat_id) or []


# Example usage and testing functions
async def example_usage():
    """Example of how to use the Value-Added Framework."""
    
    # Initialize framework
    framework = ValueAddedFramework()
    
    # Start session
    chat_id = framework.start_session()
    print(f"Session started with ID: {chat_id}")
    
    # Process some example messages
    test_messages = [
        "Hello, I'm feeling anxious about work today.",
        "I've been having trouble sleeping because I keep thinking about my presentation tomorrow.",
        "Sometimes I feel like I'm not good enough at my job."
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = await framework.process_user_message(message)
        print(f"Therapist: {response['patient_response']}")
        print(f"Clinical Notes: {response['psychiatrist_thoughts']}")
        print(f"Time Left: {response['time_left']}")
    
    # Get session summary
    summary = framework.end_session()
    print(f"\nSession Summary: {summary}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())