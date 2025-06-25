#!/usr/bin/env python3
"""
Value-Added Framework Utility Functions

This module provides utility functions for the Value-Added Prompt Framework,
including time tracking, session management, and context enhancement.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json


class SessionTimer:
    """Manages session timing and provides time-left calculations."""
    
    def __init__(self, session_duration_minutes: int = 50):
        """
        Initialize session timer.
        
        Args:
            session_duration_minutes: Total session duration in minutes (default: 50)
        """
        self.session_duration = session_duration_minutes * 60  # Convert to seconds
        self.start_time = None
        self.end_time = None
        
    def start_session(self):
        """Start the session timer."""
        self.start_time = time.time()
        self.end_time = self.start_time + self.session_duration
        
    def get_time_left(self) -> Dict[str, int]:
        """
        Get remaining time in the session.
        
        Returns:
            Dict with 'minutes' and 'seconds' remaining
        """
        if not self.start_time:
            return {"minutes": 0, "seconds": 0}
            
        current_time = time.time()
        time_left = max(0, self.end_time - current_time)
        
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        
        return {"minutes": minutes, "seconds": seconds}
    
    def get_time_left_string(self) -> str:
        """
        Get formatted time left string.
        
        Returns:
            Formatted string like "25 minutes and 30 seconds"
        """
        time_left = self.get_time_left()
        return f"{time_left['minutes']} minutes and {time_left['seconds']} seconds"
    
    def is_session_active(self) -> bool:
        """Check if the session is still active."""
        if not self.start_time:
            return False
        return time.time() < self.end_time
    
    def get_elapsed_time(self) -> Dict[str, int]:
        """
        Get elapsed time since session start.
        
        Returns:
            Dict with elapsed 'minutes' and 'seconds'
        """
        if not self.start_time:
            return {"minutes": 0, "seconds": 0}
            
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        
        return {"minutes": minutes, "seconds": seconds}


def get_default_patient_history() -> Dict[str, Any]:
    """
    Get default dummy patient history.
    
    Returns:
        Default patient history data
    """
    return {
        "patient_id": "PAT001",
        "name": "Alex Johnson",
        "age": 28,
        "previous_sessions": [
            {
                "session_number": 1,
                "date": "2024-06-18",
                "key_topics": ["work stress", "anxiety", "sleep issues"],
                "notes": "Patient reports high stress levels at work, difficulty sleeping. Discussed coping mechanisms."
            },
            {
                "session_number": 2,
                "date": "2024-06-11",
                "key_topics": ["relationship concerns", "communication"],
                "notes": "Explored relationship dynamics with partner. Worked on communication strategies."
            }
        ],
        "diagnosis": "Generalized Anxiety Disorder",
        "medications": ["Sertraline 50mg daily"],
        "therapy_goals": [
            "Reduce anxiety symptoms",
            "Improve sleep quality",
            "Develop healthy coping strategies",
            "Enhance work-life balance"
        ],
        "triggers": ["work deadlines", "conflict situations", "social gatherings"],
        "strengths": ["intelligent", "motivated", "good insight", "supportive family"]
    }


def format_patient_history(history: Dict[str, Any]) -> str:
    """
    Format patient history into a readable string for prompt injection.
    
    Args:
        history: Patient history dictionary
        
    Returns:
        Formatted history string
    """
    formatted = f"""
Patient: {history.get('name', 'Unknown')} (Age: {history.get('age', 'Unknown')})
Diagnosis: {history.get('diagnosis', 'None specified')}
Current Medications: {', '.join(history.get('medications', []))}

Therapy Goals:
{chr(10).join(f"- {goal}" for goal in history.get('therapy_goals', []))}

Known Triggers:
{', '.join(history.get('triggers', []))}

Patient Strengths:
{', '.join(history.get('strengths', []))}

Previous Sessions Summary:
"""
    
    for session in history.get('previous_sessions', []):
        formatted += f"""
Session {session.get('session_number', 'Unknown')} ({session.get('date', 'Unknown date')}):
- Topics: {', '.join(session.get('key_topics', []))}
- Notes: {session.get('notes', 'No notes available')}
"""
    
    return formatted.strip()


def create_enhanced_user_input(
    latest_message: str,
    timer: SessionTimer,
    current_session: int,
    patient_history: Dict[str, Any]
) -> str:
    """
    Create enhanced user input with context injection.
    
    Args:
        latest_message: The user's latest message
        timer: SessionTimer instance
        current_session: Current session number
        patient_history: Patient history data
        
    Returns:
        Enhanced user input string
    """
    time_left = timer.get_time_left_string()
    formatted_history = format_patient_history(patient_history)
    
    enhanced_input = f"""
Latest_Patient_Message: {{{latest_message}}};

Time_Left_In_Session: {{{time_left}}};

Current_Session: {{Session {current_session}}};

Patient_History: {{{formatted_history}}};
"""
    
    return enhanced_input.strip()


def get_system_prompt() -> str:
    """
    Get the system prompt for the psychology bot.
    
    Returns:
        System prompt string
    """
    return """You are a psychology bot. You are currently in session with the patient.

You will receive enhanced user input that includes:
- Latest_Patient_Message: The patient's current message
- Time_Left_In_Session: How much time remains in the current session
- Current_Session: Which session number this is
- Patient_History: Complete patient background and previous session notes

Instructions:
1. Always respond as a professional, empathetic psychologist
2. Be aware of the time remaining and adjust your responses accordingly
3. Reference previous sessions and patient history when relevant
4. If time is running low (under 5 minutes), start preparing for session closure
5. Maintain professional boundaries and therapeutic rapport
6. Use evidence-based therapeutic techniques when appropriate

You MUST respond in JSON format with exactly this structure:
{
    "response": "Your therapeutic response to the patient here",
    "psychiatrist_thoughts": "Your internal clinical thoughts and observations here"
}

The 'response' field should contain what you would say directly to the patient.
The 'psychiatrist_thoughts' field should contain your clinical observations, treatment planning thoughts, and session notes that the patient would not see.

Adapt your therapeutic approach based on the time remaining in the session and the patient's presenting concerns."""


def create_session_start_message() -> Dict[str, str]:
    """
    Create the initial message when a user enters the chat.
    
    Returns:
        Initial message dictionary
    """
    return {
        "role": "user",
        "content": "The User is just entering the chat."
    }


def validate_enhanced_input(enhanced_input: str) -> bool:
    """
    Validate that enhanced input contains all required components.
    
    Args:
        enhanced_input: The enhanced input string
        
    Returns:
        True if valid, False otherwise
    """
    required_components = [
        "Latest_Patient_Message:",
        "Time_Left_In_Session:",
        "Current_Session:",
        "Patient_History:"
    ]
    
    return all(component in enhanced_input for component in required_components)


def extract_session_metrics(timer: SessionTimer) -> Dict[str, Any]:
    """
    Extract session metrics for analysis.
    
    Args:
        timer: SessionTimer instance
        
    Returns:
        Dict containing session metrics
    """
    elapsed = timer.get_elapsed_time()
    remaining = timer.get_time_left()
    
    return {
        "session_active": timer.is_session_active(),
        "elapsed_minutes": elapsed["minutes"],
        "elapsed_seconds": elapsed["seconds"],
        "remaining_minutes": remaining["minutes"],
        "remaining_seconds": remaining["seconds"],
        "total_duration_minutes": timer.session_duration // 60,
        "completion_percentage": round((elapsed["minutes"] * 60 + elapsed["seconds"]) / timer.session_duration * 100, 2)
    }