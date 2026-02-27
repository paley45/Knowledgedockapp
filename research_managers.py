import sqlite3
from database import DatabaseManager

class ProjectManager:
    """Manages research projects and collections"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_manager = DatabaseManager()
            self.db_path = db_manager.db_path
        else:
            self.db_path = db_path
            
    def create_project(self, name, description=""):
        """Create a new research project"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO projects (name, description)
                    VALUES (?, ?)
                ''', (name, description))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error creating project: {e}")
            return False
            
    def get_all_projects(self):
        """Get all active projects"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, name, description, status, created_date, updated_date
                    FROM projects
                    ORDER BY updated_date DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting projects: {e}")
            return []
            
    def delete_project(self, project_id):
        """Delete a project and its resources"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM project_resources WHERE project_id = ?', (project_id,))
                cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False
            
    def add_resource_to_project(self, project_id, resource_url, resource_title):
        """Add a resource to a project"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO project_resources (project_id, resource_url, resource_title)
                    VALUES (?, ?, ?)
                ''', (project_id, resource_url, resource_title))
                
                # Update project modified date
                cursor.execute('UPDATE projects SET updated_date = CURRENT_TIMESTAMP WHERE id = ?', (project_id,))
                
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Already in project
            return True
        except Exception as e:
            print(f"Error adding resource to project: {e}")
            return False
            
    def get_project_resources(self, project_id):
        """Get all resources for a specific project"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, resource_url, resource_title, status, added_date
                    FROM project_resources
                    WHERE project_id = ?
                    ORDER BY added_date DESC
                ''', (project_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error getting project resources: {e}")
            return []
            
    def update_resource_status(self, resource_id, new_status):
        """Update status of a resource within a project"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE project_resources SET status = ? WHERE id = ?', (new_status, resource_id))
                conn.commit()
            return True
        except Exception:
            return False
            
    def get_projects_for_resource(self, resource_url):
        """Get all projects that contain a specific resource"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.id, p.name 
                    FROM projects p
                    JOIN project_resources pr ON p.id = pr.project_id
                    WHERE pr.resource_url = ?
                ''', (resource_url,))
                return cursor.fetchall()
        except Exception:
            return []


class TagManager:
    """Manages smart tags for resources"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_manager = DatabaseManager()
            self.db_path = db_manager.db_path
        else:
            self.db_path = db_path
            
    def create_tag(self, name, color="#3b82f6"):
        """Create a new tag"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO tags (name, color) VALUES (?, ?)', (name, color))
                tag_id = cursor.lastrowid
                conn.commit()
            return tag_id
        except sqlite3.IntegrityError:
            # Tag already exists, return its ID
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id FROM tags WHERE name = ?', (name,))
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error creating tag: {e}")
            return None
            
    def get_all_tags(self):
        """Get all available tags"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, color FROM tags ORDER BY name')
                return cursor.fetchall()
        except Exception:
            return []
            
    def add_tag_to_resource(self, resource_url, tag_name, color="#3b82f6"):
        """Tag a resource"""
        tag_id = self.create_tag(tag_name, color)
        if not tag_id:
            return False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO resource_tags (tag_id, resource_url)
                    VALUES (?, ?)
                ''', (tag_id, resource_url))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return True # Already tagged
        except Exception as e:
            print(f"Error tagging resource: {e}")
            return False
            
    def get_tags_for_resource(self, resource_url):
        """Get all tags for a specific resource"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT t.id, t.name, t.color
                    FROM tags t
                    JOIN resource_tags rt ON t.id = rt.tag_id
                    WHERE rt.resource_url = ?
                ''', (resource_url,))
                return cursor.fetchall()
        except Exception:
            return []
            
    def remove_tag_from_resource(self, resource_url, tag_id):
        """Remove a tag from a resource"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM resource_tags WHERE tag_id = ? AND resource_url = ?', (tag_id, resource_url))
                conn.commit()
            return True
        except Exception:
            return False


class AnnotationManager:
    """Manages notes and highlights for resources"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_manager = DatabaseManager()
            self.db_path = db_manager.db_path
        else:
            self.db_path = db_path
            
    def add_annotation(self, resource_url, note_text="", highlight_text=""):
        """Add a note or highlight to a resource"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO annotations (resource_url, note_text, highlight_text)
                    VALUES (?, ?, ?)
                ''', (resource_url, note_text, highlight_text))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error adding annotation: {e}")
            return False
            
    def get_annotations_for_resource(self, resource_url):
        """Get all notes and highlights for a resource"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, note_text, highlight_text, created_date, updated_date
                    FROM annotations
                    WHERE resource_url = ?
                    ORDER BY created_date DESC
                ''', (resource_url,))
                return cursor.fetchall()
        except Exception:
            return []
            
    def update_annotation(self, annotation_id, note_text):
        """Update an existing note"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE annotations 
                    SET note_text = ?, updated_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (note_text, annotation_id))
                conn.commit()
            return True
        except Exception:
            return False
            
    def delete_annotation(self, annotation_id):
        """Delete an annotation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM annotations WHERE id = ?', (annotation_id,))
                conn.commit()
            return True
        except Exception:
            return False
