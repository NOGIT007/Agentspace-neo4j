import re
import logging
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

# Configure logging
logger = logging.getLogger(__name__)

def is_destructive_intent(user_message: str) -> bool:
    """
    Fast analysis to detect destructive intent in user queries.
    Uses regex and contextual analysis to distinguish between read and write operations.
    
    Args:
        user_message: The user's natural language query
        
    Returns:
        True if the message contains destructive intent, False otherwise
    """
    if not user_message:
        return False
    
    message_lower = user_message.lower()
    
    # Destructive action patterns - more precise to avoid false positives
    destructive_patterns = [
        r'\bcreate\s+(new\s+)?(user|customer|product|order|record|node|database|table)',  # explicit create operations
        r'\badd\s+(new\s+)?(user|customer|product|order|record|entry)',  # explicit add operations  
        r'\binsert\s+(into\s+)?\w+',  # insert operations
        r'\bupdate\s+(the\s+)?(user|customer|product|order|record|database|table)',  # explicit update operations
        r'\bmodify\s+(the\s+)?(user|customer|product|order|record|database|table)',  # explicit modify operations
        r'\bdelete\s+(\w+\s+)*(user|customer|product|order|record|data|from)',  # explicit delete operations
        r'\bremove\s+(\w+\s+)*(user|customer|product|order|record|data|from)',  # explicit remove operations
        r'\bdrop\s+(table|database|index|constraint|user)',  # drop schema elements
        r'\bset\s+\w+\s*=',  # set property operations
        r'\bmerge\s+(into\s+)?\w+',  # merge operations
    ]
    
    # Check for destructive patterns
    for pattern in destructive_patterns:
        if re.search(pattern, message_lower):
            # Additional context check for false positives
            if not _is_safe_context(user_message, pattern):
                return True
    
    # Direct destructive keywords
    destructive_keywords = [
        'insert into', 'create node', 'delete from', 'remove node',
        'modify data', 'change database', 'update database', 'alter table'
    ]
    
    return any(keyword in message_lower for keyword in destructive_keywords)

def _is_safe_context(message: str, matched_pattern: str) -> bool:
    """
    Check if a matched destructive pattern is in a safe context (asking for information).
    
    Args:
        message: The full user message
        matched_pattern: The regex pattern that matched
        
    Returns:
        True if the context is safe (informational), False if destructive
    """
    message_lower = message.lower()
    
    # Safe context indicators for queries
    safe_indicators = [
        'how to', 'how do i', 'can you show', 'what is', 'tell me about',
        'explain', 'describe', 'example of', 'information about',
        'update me', 'keep me updated', 'status update'
    ]
    
    # Safe query patterns that might contain potentially destructive words
    safe_query_patterns = [
        r'\b(list|show|find|get|fetch|display|retrieve)\b',  # Query verbs
        r'\border\s+by\b',  # SQL/Cypher ORDER BY clause
        r'\bgroup\s+by\b',  # SQL/Cypher GROUP BY clause
        r'\bcount\b.*\bby\b',  # Count aggregations
        r'\bsum\b.*\bby\b',  # Sum aggregations
        r'\btotal\b.*\bby\b',  # Total calculations
        r'\ball\s+\w+\s+order\b',  # "all X order" patterns
        r'\bsubscription\b.*\border\b',  # Subscription order queries
    ]
    
    # Check for safe query patterns first
    for pattern in safe_query_patterns:
        if re.search(pattern, message_lower):
            return True
    
    # Check for general safe indicators
    return any(indicator in message_lower for indicator in safe_indicators)

def get_reformulation_suggestion(user_message: str) -> str:
    """
    Provide helpful suggestions for reformulating destructive queries into read operations.
    
    Args:
        user_message: The original user message with destructive intent
        
    Returns:
        A helpful suggestion for reformulating the query
    """
    message_lower = user_message.lower()
    
    if 'create' in message_lower or 'add' in message_lower:
        return "Instead, try: 'Show me existing records' or 'List current data'"
    elif 'update' in message_lower or 'modify' in message_lower:
        return "Instead, try: 'Show me the current values' or 'Display records that need updating'"
    elif 'delete' in message_lower or 'remove' in message_lower:
        return "Instead, try: 'Show me records to review' or 'List items matching criteria'"
    else:
        return "Try rephrasing as: 'Show me...', 'List...', 'Find...', or 'Count...'"

def query_security_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """
    Security callback function that intercepts queries before they reach the LLM.
    Analyzes user intent and blocks destructive operations with helpful suggestions.
    
    Args:
        callback_context: The callback context from ADK
        llm_request: The LLM request containing the user message
        
    Returns:
        LlmResponse with security message if blocked, None to allow normal processing
    """
    try:
        # Extract user message from the request
        user_message = ""
        if hasattr(llm_request, 'contents') and llm_request.contents:
            # Get the latest user content
            for content in reversed(llm_request.contents):
                if hasattr(content, 'parts') and content.parts:
                    for part in content.parts:
                        if hasattr(part, 'text') and part.text:
                            user_message = part.text
                            break
                    if user_message:
                        break
        
        if not user_message:
            # If we can't extract the message, allow processing
            return None
        
        # Fast security analysis
        if is_destructive_intent(user_message):
            suggestion = get_reformulation_suggestion(user_message)
            
            security_message = (
                "🔒 Security Alert: I can only help with reading and analyzing data from your Neo4j database. "
                f"I cannot perform write, update, or delete operations.\n\n"
                f"💡 {suggestion}\n\n"
                "I can help you with:\n"
                "• Querying and displaying data\n"
                "• Counting and aggregating records\n"
                "• Finding patterns and relationships\n"
                "• Generating reports and summaries"
            )
            
            logger.warning(f"Blocked destructive query intent: {user_message[:100]}...")
            
            # Return a security response that blocks further processing
            return LlmResponse(
                content=types.Content(parts=[types.Part(text=security_message)])
            )
        
        # Allow normal processing for safe queries
        return None
        
    except Exception as e:
        logger.error(f"Error in security callback: {e}")
        # On error, allow processing to continue (fail open for availability)
        return None