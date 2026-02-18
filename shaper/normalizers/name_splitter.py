"""
Name splitting utility

Splits full names into first/last names with basic heuristics.
"""

from typing import Tuple


def split_name(full_name: str) -> Tuple[str, str]:
    """
    Split a full name into first and last name.

    Uses simple heuristics:
    - First word = first name
    - Last word = last name
    - Middle names/initials ignored

    Args:
        full_name: Full name string (e.g., "John Doe" or "Jane Mary Smith")

    Returns:
        Tuple of (first_name, last_name)

    Examples:
        >>> split_name("John Doe")
        ("John", "Doe")

        >>> split_name("Jane Mary Smith")
        ("Jane", "Smith")

        >>> split_name("Madonna")
        ("Madonna", "")
    """
    if not full_name or not isinstance(full_name, str):
        return ('', '')

    # Clean and split
    parts = full_name.strip().split()

    if not parts:
        return ('', '')

    if len(parts) == 1:
        # Single name (e.g., "Madonna")
        return (parts[0], '')

    # Multiple parts: first word + last word
    first_name = parts[0]
    last_name = parts[-1]

    return (first_name, last_name)
