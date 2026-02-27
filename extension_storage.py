"""
Enhanced extension storage system for Knowledgedock
Handles extension data, caching, and offline access
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional


class ExtensionCacheManager:
    """Manages caching of extension search results for offline access"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_cache_tables()
    
    def init_cache_tables(self):
        """Create cache-related tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Cache settings per extension
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS extension_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extension_name TEXT NOT NULL UNIQUE,
                cache_enabled BOOLEAN DEFAULT 1,
                cache_max_results INTEGER DEFAULT 100,
                cache_ttl_hours INTEGER DEFAULT 24,
                last_sync TIMESTAMP,
                FOREIGN KEY (extension_name) REFERENCES extensions(name)
            )
        ''')
        
        # Cached search results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extension_name TEXT NOT NULL,
                query TEXT NOT NULL,
                results_json TEXT,
                cached_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (extension_name) REFERENCES extensions(name),
                UNIQUE(extension_name, query)
            )
        ''')
        
        # User library (personal collection)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                extension_name TEXT,
                status TEXT DEFAULT 'unread',  -- unread, reading, completed
                progress_percent INTEGER DEFAULT 0,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_started TIMESTAMP,
                date_completed TIMESTAMP,
                notes TEXT,
                UNIQUE(source_id)
            )
        ''')
        
        # Source metadata (enriched source data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS source_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL UNIQUE,
                extension_name TEXT NOT NULL,
                full_metadata TEXT,  -- JSON with full details
                cached_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (extension_name) REFERENCES extensions(name)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def cache_search_results(self, extension_name: str, query: str, results_json: str, ttl_hours: int = 24):
        """Cache search results from an extension"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
            
            cursor.execute('''
                INSERT OR REPLACE INTO search_cache 
                (extension_name, query, results_json, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (extension_name, query, results_json, expires_at))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error caching search results: {e}")
            return False
    
    def get_cached_results(self, extension_name: str, query: str) -> Optional[str]:
        """Get cached search results if not expired"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT results_json FROM search_cache
                WHERE extension_name = ? AND query = ? AND expires_at > datetime('now')
            ''', (extension_name, query))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting cached results: {e}")
            return None
    
    def clear_expired_cache(self):
        """Remove expired cached results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM search_cache WHERE expires_at < datetime('now')")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error clearing expired cache: {e}")
            return False
    
    def set_extension_settings(self, extension_name: str, cache_enabled: bool = True, 
                               cache_max_results: int = 100, cache_ttl_hours: int = 24):
        """Configure caching settings for an extension"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO extension_settings
                (extension_name, cache_enabled, cache_max_results, cache_ttl_hours)
                VALUES (?, ?, ?, ?)
            ''', (extension_name, cache_enabled, cache_max_results, cache_ttl_hours))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error setting extension settings: {e}")
            return False


class UserLibraryManager:
    """Manages user's personal library - downloaded and bookmarked resources"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def add_to_library(self, source_id: str, title: str, author: str, extension_name: str):
        """Add a resource to user's library"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_library
                (source_id, title, author, extension_name, status)
                VALUES (?, ?, ?, ?, 'unread')
            ''', (source_id, title, author, extension_name))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding to library: {e}")
            return False
    
    def update_progress(self, source_id: str, status: str, progress_percent: int = 0):
        """Update reading progress"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status == "reading" and progress_percent > 0:
                cursor.execute('''
                    UPDATE user_library
                    SET status = ?, progress_percent = ?, date_started = COALESCE(date_started, datetime('now'))
                    WHERE source_id = ?
                ''', (status, progress_percent, source_id))
            elif status == "completed":
                cursor.execute('''
                    UPDATE user_library
                    SET status = ?, progress_percent = 100, date_completed = datetime('now')
                    WHERE source_id = ?
                ''', (status, source_id))
            else:
                cursor.execute('''
                    UPDATE user_library
                    SET status = ?, progress_percent = ?
                    WHERE source_id = ?
                ''', (status, progress_percent, source_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating progress: {e}")
            return False
    
    def get_library(self, status: Optional[str] = None) -> List[tuple]:
        """Get user's library, optionally filtered by status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT id, source_id, title, author, extension_name, status, progress_percent, date_added
                    FROM user_library
                    WHERE status = ?
                    ORDER BY date_added DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT id, source_id, title, author, extension_name, status, progress_percent, date_added
                    FROM user_library
                    ORDER BY date_added DESC
                ''')
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"Error getting library: {e}")
            return []
    
    def add_note(self, source_id: str, note: str):
        """Add notes to a library item"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_library
                SET notes = ?
                WHERE source_id = ?
            ''', (note, source_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding note: {e}")
            return False
    
    def get_reading_stats(self) -> Dict:
        """Get reading statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM user_library')
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_library WHERE status = 'reading'")
            reading = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_library WHERE status = 'completed'")
            completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_library WHERE status = 'unread'")
            unread = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(progress_percent) FROM user_library WHERE status = 'reading'")
            avg_progress = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_items': total,
                'currently_reading': reading,
                'completed': completed,
                'unread': unread,
                'avg_progress': round(avg_progress, 1)
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}


class OfflineResourceManager:
    """Manages offline access to downloaded resources"""
    
    def __init__(self, db_path, downloads_dir):
        self.db_path = db_path
        self.downloads_dir = Path(downloads_dir)
    
    def get_available_offline(self) -> List[tuple]:
        """Get all resources available offline"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT d.id, d.source_id, d.title, d.file_path, d.extension_name, d.file_size, d.downloaded_date
                FROM downloads d
                WHERE d.status = 'completed' AND d.file_path NOT NULL
                ORDER BY d.downloaded_date DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"Error getting offline resources: {e}")
            return []
    
    def get_offline_storage_size(self) -> int:
        """Get total size of downloaded resources"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT SUM(file_size) FROM downloads WHERE status = "completed"')
            total = cursor.fetchone()[0] or 0
            
            conn.close()
            return total
        except Exception as e:
            print(f"Error getting storage size: {e}")
            return 0
    
    def is_resource_available_offline(self, source_id: str) -> bool:
        """Check if a resource is available offline"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_path FROM downloads 
                WHERE source_id = ? AND status = 'completed'
            ''', (source_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                file_path = Path(result[0])
                return file_path.exists()
            
            return False
        except Exception as e:
            print(f"Error checking offline availability: {e}")
            return False
    
    def cleanup_deleted_files(self):
        """Remove database entries for deleted files"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, file_path FROM downloads WHERE status = "completed"')
            downloads = cursor.fetchall()
            
            deleted_count = 0
            for download_id, file_path in downloads:
                if not Path(file_path).exists():
                    cursor.execute('DELETE FROM downloads WHERE id = ?', (download_id,))
                    deleted_count += 1
            
            conn.commit()
            conn.close()
            return deleted_count
        except Exception as e:
            print(f"Error cleaning up files: {e}")
            return 0


class SyncManager:
    """Manages syncing between extensions and local database"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def mark_sync_complete(self, extension_name: str):
        """Mark an extension as recently synced"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE extension_settings
                SET last_sync = datetime('now')
                WHERE extension_name = ?
            ''', (extension_name,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking sync: {e}")
            return False
    
    def needs_resync(self, extension_name: str) -> bool:
        """Check if extension needs resync based on TTL"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT last_sync, cache_ttl_hours FROM extension_settings
                WHERE extension_name = ?
            ''', (extension_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return True
            
            last_sync, ttl = result
            if not last_sync:
                return True
            
            last_sync_time = datetime.fromisoformat(last_sync)
            return datetime.now() - last_sync_time > timedelta(hours=ttl)
        except Exception as e:
            print(f"Error checking resync: {e}")
            return True
