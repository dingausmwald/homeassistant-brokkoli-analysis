"""Processors module for image analysis."""

from .base import BaseProcessor
from .green_pixels_processor import GreenPixelsProcessor

__all__ = ['BaseProcessor', 'GreenPixelsProcessor'] 