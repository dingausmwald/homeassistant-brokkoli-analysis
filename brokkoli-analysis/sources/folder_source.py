"""Folder source for monitoring image directories."""

import os
import logging
import time
from typing import Optional
from pathlib import Path
import numpy as np
import cv2
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .base import BaseSource

logger = logging.getLogger(__name__)


class ImageHandler(FileSystemEventHandler):
    """Handler for file system events in image directories."""
    
    def __init__(self, folder_source):
        self.folder_source = folder_source
        
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self.folder_source._handle_new_file(event.src_path)
            
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self.folder_source._handle_new_file(event.src_path)


class FolderSource(BaseSource):
    """Source for monitoring image files in a directory."""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def __init__(self, name: str, config: dict):
        """Initialize folder source.
        
        Args:
            name: Name of the source
            config: Configuration with 'path' and 'update_interval'
        """
        super().__init__(name, config)
        self.path = Path(config['path'])
        self.update_interval = config.get('update_interval', 30)
        self.observer = None
        self.latest_image_path = None
        self.latest_image_time = 0
        self.has_new = False
        
        # Ensure directory exists
        self.path.mkdir(parents=True, exist_ok=True)
        
    def start(self):
        """Start monitoring the directory."""
        if not self.enabled:
            return
            
        logger.info(f"Starting folder monitoring for {self.path}")
        
        # Set up file system observer
        self.observer = Observer()
        handler = ImageHandler(self)
        self.observer.schedule(handler, str(self.path), recursive=False)
        self.observer.start()
        
        # Check for existing images
        self._scan_for_latest_image()
        
    def stop(self):
        """Stop monitoring the directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
    def _handle_new_file(self, file_path: str):
        """Handle new file detection."""
        if self._is_image_file(file_path):
            logger.debug(f"New image detected: {file_path}")
            self.latest_image_path = file_path
            self.latest_image_time = time.time()
            self.has_new = True
            
    def _is_image_file(self, file_path: str) -> bool:
        """Check if file is a supported image format."""
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS
        
    def _scan_for_latest_image(self):
        """Scan directory for the most recent image."""
        if not self.path.exists():
            return
            
        image_files = []
        for file_path in self.path.iterdir():
            if file_path.is_file() and self._is_image_file(str(file_path)):
                image_files.append(file_path)
                
        if image_files:
            # Get most recent file
            latest_file = max(image_files, key=lambda f: f.stat().st_mtime)
            self.latest_image_path = str(latest_file)
            self.latest_image_time = latest_file.stat().st_mtime
            self.has_new = True
            logger.info(f"Found latest image: {latest_file}")
            
    def has_new_image(self) -> bool:
        """Check if there's a new image available."""
        return self.has_new
        
    def get_latest_image(self) -> Optional[np.ndarray]:
        """Get the latest image from the directory."""
        if not self.latest_image_path or not os.path.exists(self.latest_image_path):
            return None
            
        try:
            # Load image using OpenCV
            image = cv2.imread(self.latest_image_path)
            if image is not None:
                # Convert BGR to RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.has_new = False  # Mark as consumed
                logger.debug(f"Loaded image: {self.latest_image_path}, shape: {image.shape}")
                return image
            else:
                logger.error(f"Failed to load image: {self.latest_image_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading image {self.latest_image_path}: {e}")
            return None 