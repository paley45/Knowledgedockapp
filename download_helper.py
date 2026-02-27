"""
Download manager for Knowledgedock
Handles downloading PDFs, books, and other resources
"""

import os
import requests
from pathlib import Path
from urllib.parse import urlparse
from constants import DOWNLOADS_DIR
from utils.logger import logger

class DownloadHelper:
    """Helper class for downloading resources"""
    
    def __init__(self, download_dir: str = None):
        if download_dir is None:
            self.download_dir = DOWNLOADS_DIR
        else:
            self.download_dir = Path(download_dir)
        
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url: str, filename: str = None, progress_callback=None) -> tuple[bool, str]:
        """
        Download a file from URL
        
        Returns:
            (success: bool, message: str)
        """
        try:
            if not url or not url.startswith(('http://', 'https://')):
                logger.error(f"Invalid URL: {url}")
                return False, "Invalid URL"
            
            # Determine filename
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = "download"
            
            # Clean filename
            filename = self.clean_filename(filename)
            file_path = self.download_dir / filename
            
            # Check if file already exists
            if file_path.exists():
                logger.info(f"File already exists: {file_path}")
                return True, f"File already exists at:\n{file_path}"
            
            logger.info(f"Starting download: {url} -> {file_path}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,image/webp,*/*;q=0.8'
            }
            # Download with progress
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            # Ensure progress callback doesn't block
                            try:
                                progress_callback(progress)
                            except Exception:
                                pass
            
            logger.info(f"Download complete: {file_path}")
            return True, f"Downloaded successfully to:\n{file_path}"
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during download: {e}")
            return False, f"Download failed: {str(e)}"
        except Exception as e:
            logger.exception(f"Unexpected error during download: {e}")
            return False, f"Error: {str(e)}"
    
    def download_pdf_from_arxiv(self, arxiv_id: str, progress_callback=None) -> tuple[bool, str]:
        """Download PDF from arXiv"""
        if not arxiv_id:
            return False, "Invalid arXiv ID"
        
        # arXiv PDF URL format
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        filename = f"{arxiv_id}.pdf"
        
        return self.download_file(pdf_url, filename, progress_callback)
    
    def download_book_from_openlibrary(self, book_key: str, progress_callback=None) -> tuple[bool, str]:
        """Download book from Open Library"""
        if not book_key:
            return False, "Invalid book key"
        
        # Try to get book details first
        try:
            api_url = f"https://openlibrary.org{book_key}.json"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Look for available download links
            if 'url' in data:
                filename = data.get('title', 'book')
                return self.download_file(data['url'], f"{filename}.pdf", progress_callback)
            else:
                return False, "No downloadable version available for this book on Open Library"
        
        except Exception as e:
            logger.error(f"Open Library download error: {e}")
            return False, f"Could not download from Open Library: {str(e)}"
    
    def download_from_gutenberg(self, book_id: str, format_type: str = 'epub', progress_callback=None) -> tuple[bool, str]:
        """Download book from Project Gutenberg"""
        if not book_id:
            return False, "Invalid book ID"
        
        # Project Gutenberg download URL format
        supported_formats = {
            'epub': f"https://www.gutendex.com/cache/epub/{book_id}/pg{book_id}.epub",
            'html': f"https://www.gutendex.com/cache/epub/{book_id}/pg{book_id}-h/pg{book_id}-h.htm",
            'txt': f"https://www.gutendex.com/cache/epub/{book_id}/pg{book_id}.txt"
        }
        
        if format_type not in supported_formats:
            format_type = 'epub'
        
        url = supported_formats[format_type]
        filename = f"gutenberg_{book_id}.{format_type}"
        
        return self.download_file(url, filename, progress_callback)
    
    def download_wikipedia_article(self, title: str, progress_callback=None) -> tuple[bool, str]:
        """Download Wikipedia article as HTML"""
        if not title:
            return False, "Invalid article title"
        
        # Wikipedia offline download URL
        url = f"https://en.wikipedia.org/wiki/Special:Export/{title}"
        filename = f"wikipedia_{title.replace(' ', '_')}.html"
        
        return self.download_file(url, filename, progress_callback)
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean filename to remove invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:195] + ('.' + ext if ext else '')
        
        return filename
    
    def get_downloads_path(self) -> Path:
        """Get the downloads directory path"""
        return self.download_dir
    
    def open_downloads_folder(self) -> bool:
        """Open the downloads folder in file explorer"""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(self.download_dir)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', self.download_dir])
            else:
                subprocess.Popen(['xdg-open', self.download_dir])
            
            return True
        except Exception as e:
            logger.error(f"Failed to open downloads folder: {e}")
            return False
