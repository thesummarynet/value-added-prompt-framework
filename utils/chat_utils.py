#!/usr/bin/env python3
"""
Chat Utility Functions

This module provides utility functions for managing chats with TinyDB,
including creating, fetching, and updating chats.
"""

import uuid
import json
from typing import List, Dict, Any, Optional, Union
from tinydb import TinyDB, Query
from tinydb.operations import set


def begin_chat(db_name: str) -> str:
    """
    Start a new chat and return its ID.
    
    Args:
        db_name: Name of the TinyDB database file (without extension)
        
    Returns:
        New chat ID as a string
        
    Raises:
        IOError: If database cannot be accessed or created
    """
    try:
        db = TinyDB(f"{db_name}.json")
        chats_table = db.table('chats')
        
        chat_id = str(uuid.uuid4())
        chats_table.insert({
            'id': chat_id,
            'messages': []
        })
        
        return chat_id
    except Exception as e:
        print(f"Error creating new chat: {e}")
        raise IOError(f"Could not create new chat in database {db_name}: {e}")


def fetch_chat(db_name: str, chat_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch a chat by its ID.
    
    Args:
        db_name: Name of the TinyDB database file (without extension)
        chat_id: ID of the chat to fetch
        
    Returns:
        List of chat messages or None if not found
        
    Raises:
        IOError: If database cannot be accessed
    """
    try:
        db = TinyDB(f"{db_name}.json")
        chats_table = db.table('chats')
        Chat = Query()
        
        result = chats_table.get(Chat.id == chat_id)
        return result.get('messages', []) if result else None
    except Exception as e:
        print(f"Error fetching chat {chat_id}: {e}")
        raise IOError(f"Could not fetch chat from database {db_name}: {e}")


def fetch_all(db_name: str) -> List[str]:
    """
    Fetch all chat IDs.
    
    Args:
        db_name: Name of the TinyDB database file (without extension)
        
    Returns:
        List of chat IDs
        
    Raises:
        IOError: If database cannot be accessed
    """
    try:
        db = TinyDB(f"{db_name}.json")
        chats_table = db.table('chats')
        
        all_chats = chats_table.all()
        return [chat.get('id') for chat in all_chats if 'id' in chat]
    except Exception as e:
        print(f"Error fetching all chats: {e}")
        raise IOError(f"Could not fetch all chats from database {db_name}: {e}")


def add_message(db_name: str, chat_id: str, role: str, message: str) -> bool:
    """
    Add a message to a chat.
    
    Args:
        db_name: Name of the TinyDB database file (without extension)
        chat_id: ID of the chat to add the message to
        role: Role of the message sender ('user', 'assistant', 'system')
        message: Content of the message
        
    Returns:
        True if successful, False if chat not found
        
    Raises:
        IOError: If database cannot be accessed
        ValueError: If role is invalid
    """
    if role not in ['user', 'assistant', 'system']:
        raise ValueError(f"Invalid role: {role}. Must be 'user', 'assistant', or 'system'")
        
    try:
        db = TinyDB(f"{db_name}.json")
        chats_table = db.table('chats')
        Chat = Query()
        
        chat = chats_table.get(Chat.id == chat_id)
        if not chat:
            return False
        
        messages = chat.get('messages', [])
        messages.append({
            'role': role,
            'content': message
        })
        
        chats_table.update({'messages': messages}, Chat.id == chat_id)
        return True
    except Exception as e:
        print(f"Error adding message to chat {chat_id}: {e}")
        raise IOError(f"Could not add message to chat in database {db_name}: {e}")


def parse_chat(db_name: str, chat_id: str, user_replacement: str, assistant_replacement: str) -> Optional[str]:
    """
    Parse a chat into a formatted string.
    
    Args:
        db_name: Name of the TinyDB database file (without extension)
        chat_id: ID of the chat to parse
        user_replacement: String to replace 'user' roles in formatting
        assistant_replacement: String to replace 'assistant' roles in formatting
        
    Returns:
        Formatted chat string or None if chat not found
        
    Raises:
        IOError: If database cannot be accessed
    """
    try:
        messages = fetch_chat(db_name, chat_id)
        if not messages:
            return None
        
        formatted_messages = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            
            if role == 'user':
                formatted_messages.append(f"*{user_replacement}*: {content}")
            elif role == 'assistant':
                formatted_messages.append(f"*{assistant_replacement}*: {content}")
            # System messages are typically not displayed to users
        
        return " |\n| ".join(formatted_messages)
    except Exception as e:
        print(f"Error parsing chat {chat_id}: {e}")
        raise IOError(f"Could not parse chat from database {db_name}: {e}")