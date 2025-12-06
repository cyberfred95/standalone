"""
Language utility functions.
"""

def normalize_language_code(code):
    """
    Normalizes language code to UPPERCASE (e.g., 'fr-fr' -> 'FR', 'en-US' -> 'EN-US').
    All language codes in the database are stored in UPPERCASE.
    """
    if not code:
        return code

    # Convert to uppercase for consistency
    return code.upper()
