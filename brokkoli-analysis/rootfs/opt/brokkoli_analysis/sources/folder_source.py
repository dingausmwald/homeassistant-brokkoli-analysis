"""Folder source for monitoring image directories."""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .base import BaseSource


class ImageFileHandler(FileSystemEventHandler):
    """Handler for image file system events."""
    
    def __init__(self, folder_source):
        self.folder_source = folder_source
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.image_extensions:
                self.folder_source.logger.info(f"New image detected: {file_path.name}")
                self.folder_source._update_latest_image(file_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in self.image_extensions:
                self.folder_source.logger.debug(f"Image modified: {file_path.name}")
                self.folder_source._update_latest_image(file_path)


class FolderSource(BaseSource):
    """Source that monitors a folder for new images."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        self.path = Path(config['path'])
        self.update_interval = config.get('update_interval', 30)
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        self.latest_image_path: Optional[Path] = None
        self.latest_image_time: Optional[float] = None
        self.last_processed_time: Optional[float] = None
        
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[ImageFileHandler] = None
        
        # Create directory if it doesn't exist
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Find initial latest image
        self._find_latest_image()
    
    def start(self) -> None:
        """Start monitoring the folder."""
        if not self.path.exists():
            self.logger.error(f"Path does not exist: {self.path}")
            return
        
        self.event_handler = ImageFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.path), recursive=False)
        self.observer.start()
        self.logger.info(f"Started monitoring folder: {self.path}")
    
    def stop(self) -> None:
        """Stop monitoring the folder."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.logger.info("Stopped folder monitoring")
    
    def is_available(self) -> bool:
        """Check if the folder source is available."""
        return self.path.exists() and self.path.is_dir()
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the latest image from the folder."""
        if not self.latest_image_path or not self.latest_image_path.exists():
            return None
        
        # Check if we should process this image (based on update interval)
        current_time = time.time()
        if (self.last_processed_time and 
            current_time - self.last_processed_time < self.update_interval):
            return None
        
        # Check if there's a new image since last processing
        if (self.last_processed_time and self.latest_image_time and
            self.latest_image_time <= self.last_processed_time):
            return None
        
        try:
            # Load image using OpenCV
            image = cv2.imread(str(self.latest_image_path))
            if image is not None:
                # Convert BGR to RGB
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.last_processed_time = current_time
                self.logger.debug(f"Loaded image: {self.latest_image_path.name}")
                return image
        except Exception as e:
            self.logger.error(f"Error loading image {self.latest_image_path}: {e}")
        
        return None
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the current image."""
        metadata = super().get_metadata()
        
        if self.latest_image_path:
            metadata.update({
                'file_path': str(self.latest_image_path),
                'file_name': self.latest_image_path.name,
                'file_size': self.latest_image_path.stat().st_size if self.latest_image_path.exists() else 0,
                'modification_time': self.latest_image_time,
                'last_processed': self.last_processed_time
            })
        
        return metadata
    
    def _find_latest_image(self) -> None:
        """Find the latest image in the folder."""
        if not self.path.exists():
            return
        
        latest_file = None
        latest_time = 0
        
        for file_path in self.path.iterdir():
            if (file_path.is_file() and 
                file_path.suffix.lower() in self.image_extensions):
                
                mod_time = file_path.stat().st_mtime
                if mod_time > latest_time:
                    latest_time = mod_time
                    latest_file = file_path
        
        if latest_file:
            self.latest_image_path = latest_file
            self.latest_image_time = latest_time
            self.logger.info(f"Found latest image: {latest_file.name}")
    
    def _update_latest_image(self, file_path: Path) -> None:
        """Update the latest image reference."""
        if file_path.exists():
            mod_time = file_path.stat().st_mtime
            if not self.latest_image_time or mod_time > self.latest_image_time:
                self.latest_image_path = file_path
                self.latest_image_time = mod_time
                self.logger.debug(f"Updated latest image: {file_path.name}") 