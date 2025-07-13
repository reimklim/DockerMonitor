"""
Compatibility utilities for Dockify.
"""
import logging

logger = logging.getLogger('dockify.utils.compat')

def get_compatible_color(color):
    """
    Convert potential problematic color values to compatible alternatives.
    
    Args:
        color: Original color value
        
    Returns:
        Compatible color value
    """
    if color == "transparent":
        logger.debug("Converting 'transparent' to a compatible value")
        return "#000000"  # Use black instead of transparent
    return color