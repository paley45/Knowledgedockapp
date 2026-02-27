import sqlite3
import os
from datetime import datetime
from pathlib import Path
from constants import DB_PATH, DOWNLOADS_DIR


class DatabaseManager:
    """Unified database manager for Knowledgedock"""
    
    def __init__(self):
        self.downloads_dir = DOWNLOADS_DIR
        self.downloads_dir.mkdir(exist_ok=True)
        self.db_path = DB_PATH
        self.init_db()
    
    def init_db(self):
        """Initialize the database and create all tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute('PRAGMA foreign_keys = ON')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    source TEXT,
                    resource_type TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cover_url TEXT,
                    description TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extensions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    version TEXT,
                    author TEXT,
                    description TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    installed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extension_name TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT,
                    url TEXT NOT NULL,
                    source_type TEXT,
                    cover_url TEXT,
                    description TEXT,
                    tags TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (extension_name) REFERENCES extensions(name),
                    UNIQUE(extension_name, source_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    extension_name TEXT,
                    downloaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    status TEXT DEFAULT 'completed'
                )
            ''')
            
            # --- Research Dashboard Tables ---
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    status TEXT DEFAULT 'active',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    resource_url TEXT NOT NULL,
                    resource_title TEXT NOT NULL,
                    status TEXT DEFAULT 'to_read', -- 'to_read', 'reading', 'synthesized'
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    UNIQUE(project_id, resource_url)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#3b82f6',
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resource_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_id INTEGER NOT NULL,
                    resource_url TEXT NOT NULL,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
                    UNIQUE(tag_id, resource_url)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_url TEXT NOT NULL,
                    note_text TEXT,
                    highlight_text TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()


class BookmarkManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_manager = DatabaseManager()
            self.db_path = db_manager.db_path
        else:
            self.db_path = db_path
    
    def add_bookmark(self, title, url, source="", resource_type="", cover_url="", description=""):
        """Add a new bookmark"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO bookmarks (title, url, source, resource_type, cover_url, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (title, url, source, resource_type, cover_url, description))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already bookmarked
        except Exception as e:
            print(f"Error adding bookmark: {e}")
            return False
    
    def remove_bookmark(self, url):
        """Remove a bookmark by URL"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM bookmarks WHERE url = ?', (url,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error removing bookmark: {e}")
            return False
    
    def get_all_bookmarks(self):
        """Get all bookmarks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, url, source, resource_type, added_date, cover_url, description
                    FROM bookmarks
                    ORDER BY added_date DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching bookmarks: {e}")
            return []
    
    def get_bookmarks_by_source(self, source):
        """Get bookmarks from a specific source"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, url, source, resource_type, added_date, cover_url, description
                    FROM bookmarks
                    WHERE source = ?
                    ORDER BY added_date DESC
                ''', (source,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching bookmarks by source: {e}")
            return []
    
    def is_bookmarked(self, url):
        """Check if a URL is already bookmarked"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM bookmarks WHERE url = ?', (url,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking bookmark: {e}")
            return False
    
    def search_bookmarks(self, query):
        """Search bookmarks by title or description"""
        try:
            search_term = f"%{query}%"
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, title, url, source, resource_type, added_date, cover_url, description
                    FROM bookmarks
                    WHERE title LIKE ? OR description LIKE ? OR source LIKE ?
                    ORDER BY added_date DESC
                ''', (search_term, search_term, search_term))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error searching bookmarks: {e}")
            return []
    
    def get_bookmark_count(self):
        """Get total number of bookmarks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM bookmarks')
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting bookmark count: {e}")
            return 0


class ExtensionManager:
    """Manages extension data in database"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_manager = DatabaseManager()
            self.db_path = db_manager.db_path
        else:
            self.db_path = db_path
    
    def register_extension(self, name, version, author, description):
        """Register an extension in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO extensions (name, version, author, description, enabled)
                    VALUES (?, ?, ?, ?, 1)
                ''', (name, version, author, description))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error registering extension: {e}")
            return False
    
    def get_all_extensions(self):
        """Get all registered extensions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name, version, author, description, enabled, installed_date FROM extensions')
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching extensions: {e}")
            return []
    
    def enable_extension(self, name):
        """Enable an extension"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE extensions SET enabled = 1 WHERE name = ?', (name,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error enabling extension: {e}")
            return False
    
    def disable_extension(self, name):
        """Disable an extension"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE extensions SET enabled = 0 WHERE name = ?', (name,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error disabling extension: {e}")
            return False
    
    def add_source(self, extension_name, source_id, title, author, url, source_type, cover_url="", description="", tags=""):
        """Add a source from an extension"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO sources 
                    (extension_name, source_id, title, author, url, source_type, cover_url, description, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (extension_name, source_id, title, author, url, source_type, cover_url, description, tags))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding source: {e}")
            return False
    
    def get_sources_by_extension(self, extension_name):
        """Get all sources from a specific extension"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, source_id, title, author, url, source_type, cover_url, description, tags, added_date
                    FROM sources
                    WHERE extension_name = ?
                    ORDER BY added_date DESC
                ''', (extension_name,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching sources: {e}")
            return []
    
    def search_sources(self, query):
        """Search sources by title or description"""
        try:
            search_term = f"%{query}%"
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, extension_name, source_id, title, author, url, source_type, cover_url, description, tags
                    FROM sources
                    WHERE title LIKE ? OR description LIKE ? OR tags LIKE ?
                    ORDER BY added_date DESC
                    LIMIT 50
                ''', (search_term, search_term, search_term))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error searching sources: {e}")
            return []
    
    def get_all_sources(self, limit=100):
        """Get all sources from all extensions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, extension_name, source_id, title, author, url, source_type, cover_url, description, tags
                    FROM sources
                    ORDER BY added_date DESC
                    LIMIT ?
                ''', (limit,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching all sources: {e}")
            return []


class DownloadManager:
    """Manages file downloads and tracking"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_manager = DatabaseManager()
            self.db_path = db_manager.db_path
            self.downloads_dir = db_manager.downloads_dir
        else:
            self.db_path = db_path
            self.downloads_dir = DOWNLOADS_DIR  # Fixed: was hardcoded Path, now uses constants
    
    def add_download(self, source_id, title, file_path, extension_name, file_size=0):
        """Track a downloaded file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO downloads (source_id, title, file_path, extension_name, file_size, status)
                    VALUES (?, ?, ?, ?, ?, 'completed')
                ''', (source_id, title, file_path, extension_name, file_size))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding download: {e}")
            return False
    
    def get_all_downloads(self):
        """Get all downloaded files"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, source_id, title, file_path, extension_name, downloaded_date, file_size, status
                    FROM downloads
                    ORDER BY downloaded_date DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching downloads: {e}")
            return []
    
    def is_downloaded(self, source_id):
        """Check if a source is already downloaded"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM downloads WHERE source_id = ? AND status = "completed"', (source_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking download: {e}")
            return False
    
    def get_download_path(self, source_id):
        """Get the file path for a downloaded resource"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT file_path FROM downloads WHERE source_id = ? AND status = "completed"', (source_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error getting download path: {e}")
            return None