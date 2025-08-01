from django import template

register = template.Library()

@register.filter(name='split')
def split(value, delimiter):
    """
    Returns a list containing the substrings of the value
    split by the specified delimiter.
    
    Example: {{ value|split:"," }}
    """
    if value:
        return value.split(delimiter)
    return []

@register.filter(name='trim')
def trim(value):
    """
    Removes leading and trailing whitespace from the value.
    
    Example: {{ value|trim }}
    """
    if value:
        return value.strip()
    return ""

@register.filter(name='abs')
def abs_filter(value):
    """
    Returns the absolute value of a number.
    
    Example: {{ value|abs }}
    """
    try:
        if value is None:
            return 0
        # Try to convert to float first if it's a string
        if isinstance(value, str):
            value = float(value.replace('%', ''))
        return abs(value)
    except (ValueError, TypeError):
        # If conversion fails, return 0
        return 0 