"""
HTML cleaning utilities for Lara translation.
"""
import re

def clean_html_for_lara(html_content):
    """
    Cleans HTML content before sending to Lara.
    Replaces specific empty paragraph patterns with <br> tags.
    """
    if not html_content:
        return ""

    # Replace <p><br></p> with <br> (with optional spaces and / in br tag)
    cleaned = re.sub(r'<p>\s*<br\s*/?>\s*</p>', '<br>', html_content, flags=re.IGNORECASE)

    # Replace <p>&nbsp;</p> with <br> (with optional spaces)
    cleaned = re.sub(r'<p>\s*&nbsp;\s*</p>', '<br>', cleaned, flags=re.IGNORECASE)

    # Replace <p> </p> (paragraph with only spaces) with <br>
    cleaned = re.sub(r'<p>\s+</p>', '<br>', cleaned, flags=re.IGNORECASE)

    return cleaned
