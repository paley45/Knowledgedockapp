"""
Extension system for Knowledgedock
Base classes and interfaces for creating source extensions
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Resource:
    """Represents a single resource from an extension"""
    id: str
    title: str
    author: str
    url: str
    source_type: str  # "PDF", "Web", "EPUB", etc.
    cover_url: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class Extension(ABC):
    """Base class for all Knowledgedock extensions"""
    
    def __init__(self):
        self.name = "Base Extension"
        self.version = "1.0.0"
        self.author = "Unknown"
        self.description = "Extension for Knowledgedock"
        self.enabled = True
    
    @abstractmethod
    def search(self, query: str, limit: int = 20) -> List[Resource]:
        """Search for resources matching the query"""
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """Get available categories/genres"""
        pass
    
    @abstractmethod
    def get_trending(self, limit: int = 10) -> List[Resource]:
        """Get trending/popular resources"""
        pass
    
    def get_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get a specific resource by ID"""
        pass
    
    def download_resource(self, resource_id: str, save_path: str) -> bool:
        """Download a resource to local storage"""
        pass
    
    def validate(self) -> bool:
        """Validate extension integrity"""
        return True


class ExtensionManager:
    """Manages loading and interaction with extensions"""
    
    def __init__(self, extensions_dir: str):
        self.extensions_dir = extensions_dir
        self.extensions: Dict[str, Extension] = {}
    
    def register_extension(self, name: str, extension: Extension):
        """Register an extension"""
        self.extensions[name] = extension
    
    def get_extension(self, name: str) -> Optional[Extension]:
        """Get an extension by name"""
        return self.extensions.get(name)
    
    def list_extensions(self) -> List[tuple]:
        """List all registered extensions with their info"""
        return [
            (name, ext.name, ext.version, ext.enabled)
            for name, ext in self.extensions.items()
        ]
    
    def enable_extension(self, name: str):
        """Enable an extension"""
        if name in self.extensions:
            self.extensions[name].enabled = True
    
    def disable_extension(self, name: str):
        """Disable an extension"""
        if name in self.extensions:
            self.extensions[name].enabled = False
    
    def search_all(self, query: str, limit: int = 50) -> List[Dict]:
        """Search across all enabled extensions"""
        results = []
        per_extension = max(1, limit // len([e for e in self.extensions.values() if e.enabled]))
        
        for ext_name, extension in self.extensions.items():
            if not extension.enabled:
                continue
            
            try:
                ext_results = extension.search(query, limit=per_extension)
                for resource in ext_results:
                    results.append({
                        'extension': ext_name,
                        'resource': resource
                    })
            except Exception as e:
                print(f"Error searching {ext_name}: {e}")
        
        return results[:limit]
    
    def get_trending_all(self, limit: int = 20) -> List[Dict]:
        """Get trending resources from all enabled extensions"""
        results = []
        per_extension = max(1, limit // len([e for e in self.extensions.values() if e.enabled]))
        
        for ext_name, extension in self.extensions.items():
            if not extension.enabled:
                continue
            
            try:
                ext_results = extension.get_trending(limit=per_extension)
                for resource in ext_results:
                    results.append({
                        'extension': ext_name,
                        'resource': resource
                    })
            except Exception as e:
                print(f"Error getting trending from {ext_name}: {e}")
        
        return results[:limit]
