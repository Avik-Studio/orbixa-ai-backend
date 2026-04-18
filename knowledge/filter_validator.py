"""
Filter validator module for Medical Bot Agent OS.
Validates knowledge base filters to ensure they conform to the "one book per search" rule.
"""
from typing import Dict, Any, Optional


def validate_filters(filters: Optional[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
    """
    Validate knowledge base filters according to medical bot rules.
    
    Rules:
    - Only ONE book_name per search (no lists of books)
    - Valid filter keys: book_name, part, page
    - book_name must be a string if present
    - part must be a string if present
    - page must be an integer if present
    
    Args:
        filters: Dictionary of filters to validate
    
    Returns:
        tuple: (is_valid, error_message)
            - is_valid: True if filters are valid, False otherwise
            - error_message: None if valid, error description if invalid
    """
    # Empty filters are valid (searches all documents)
    if not filters:
        return True, None
    
    # Check if filters is a dictionary
    if not isinstance(filters, dict):
        return False, "Filters must be a dictionary"
    
    # Define valid filter keys
    valid_keys = {'book_name', 'part', 'page'}
    
    # Check for invalid keys
    invalid_keys = set(filters.keys()) - valid_keys
    if invalid_keys:
        return False, f"Invalid filter keys: {', '.join(invalid_keys)}. Valid keys are: {', '.join(valid_keys)}"
    
    # Validate book_name if present
    if 'book_name' in filters:
        book_name = filters['book_name']
        
        # Must be a string, not a list
        if isinstance(book_name, list):
            return False, "Multiple books in one search are not allowed. Search each book individually."
        
        # Must be a non-empty string
        if not isinstance(book_name, str):
            return False, "book_name must be a string"
        
        if not book_name.strip():
            return False, "book_name cannot be empty"
    
    # Validate part if present
    if 'part' in filters:
        part = filters['part']
        
        if not isinstance(part, str):
            return False, "part must be a string"
        
        if not part.strip():
            return False, "part cannot be empty"
    
    # Validate page if present
    if 'page' in filters:
        page = filters['page']
        
        if not isinstance(page, int):
            return False, "page must be an integer"
        
        if page < 1:
            return False, "page must be a positive integer"
    
    # All validations passed
    return True, None
