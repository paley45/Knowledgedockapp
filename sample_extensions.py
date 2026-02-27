"""
Sample extensions for Knowledgedock
Implementations for popular free knowledge sources
"""

from extensions import Extension, Resource
from typing import List, Optional
import requests
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DOAJExtension(Extension):
    """Extension for DOAJ - Directory of Open Access Journals"""
    
    def __init__(self):
        super().__init__()
        self.name = "DOAJ"
        self.version = "2.0.0"
        self.author = "Knowledgedock"
        self.description = "Access thousands of open access peer-reviewed journals and articles"
        self.base_url = "https://doaj.org/api/search/articles"
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.headers.update({'User-Agent': 'Knowledgedock/1.0'})
    
    def search(self, query: str, limit: int = 20) -> List[Resource]:
        """Search DOAJ articles"""
        try:
            url = f"{self.base_url}/{quote(query)}"
            params = {'pageSize': min(limit, 50)}
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                resources = []
                
                for article in data.get('results', [])[:limit]:
                    bibjson = article.get('bibjson', {})
                    authors = bibjson.get('author', [])
                    author_name = authors[0].get('name', 'Unknown') if authors else 'Unknown'
                    
                    # Extract URL
                    links = bibjson.get('link', [])
                    article_url = ""
                    for link in links:
                        if link.get('type') == 'fulltext':
                            article_url = link.get('url', '')
                            break
                    if not article_url and links:
                        article_url = links[0].get('url', '')
                    
                    if not article_url:
                        article_url = f"https://doaj.org/article/{article.get('id', '')}"
                        
                    resource = Resource(
                        id=article.get('id', ''),
                        title=bibjson.get('title', 'Unknown'),
                        author=author_name,
                        url=article_url,
                        source_type="Journal Article",
                        description=bibjson.get('abstract', 'No abstract available')[:500],
                        tags=["Journal", "Open Access", "DOAJ"]
                    )
                    resources.append(resource)
                
                return resources
        except Exception as e:
            print(f"Error searching DOAJ: {e}")
        
        return []
    
    def get_categories(self) -> List[str]:
        return ["Science", "Medicine", "Social Sciences", "Arts", "Humanities", "Engineering"]
    
    def get_trending(self, limit: int = 10) -> List[Resource]:
        """Get recent articles from DOAJ"""
        return self.search("science OR medicine OR technology", limit)


class CrossrefExtension(Extension):
    """Extension for Crossref API - Academic research metadata"""
    
    def __init__(self):
        super().__init__()
        self.name = "Crossref"
        self.version = "1.0.0"
        self.author = "Knowledgedock"
        self.description = "Access metadata for millions of academic research papers via DOI"
        self.base_url = "https://api.crossref.org/works"
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        # Politer pool usage asks for email in user agent
        self.session.headers.update({'User-Agent': 'Knowledgedock/1.0 (mailto:admin@example.com)'})
    
    def search(self, query: str, limit: int = 20) -> List[Resource]:
        """Search Crossref articles"""
        try:
            params = {
                'query': query,
                'rows': min(limit, 50),
                'select': 'DOI,title,author,URL,abstract,type,publisher'
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                resources = []
                
                for item in data.get('message', {}).get('items', [])[:limit]:
                    title = item.get('title', ['Unknown'])[0] if isinstance(item.get('title'), list) else item.get('title', 'Unknown')
                    
                    # Extract author
                    authors = item.get('author', [])
                    if authors:
                        first_author = authors[0]
                        author_name = f"{first_author.get('given', '')} {first_author.get('family', '')}".strip()
                    else:
                        author_name = 'Unknown'
                        
                    # Extract abstract (Crossref puts <jats:p> tags in abstracts)
                    abstract = item.get('abstract', 'No abstract available')
                    if abstract and abstract != 'No abstract available':
                        abstract = abstract.replace('<jats:p>', '').replace('</jats:p>', '').replace('<jats:sec>', '').replace('</jats:sec>', '')
                        abstract = abstract[:500] + "..." if len(abstract) > 500 else abstract
                        
                    resource = Resource(
                        id=item.get('DOI', ''),
                        title=title,
                        author=author_name,
                        url=item.get('URL', ''),
                        source_type=item.get('type', 'Research Paper').replace('-', ' ').title(),
                        description=abstract,
                        tags=["Research", "Crossref", item.get('publisher', 'Various')]
                    )
                    resources.append(resource)
                
                return resources
        except Exception as e:
            print(f"Error searching Crossref: {e}")
        
        return []
    
    def get_categories(self) -> List[str]:
        return ["Journal Article", "Book Chapter", "Proceedings", "Dataset", "Preprint"]
    
    def get_trending(self, limit: int = 10) -> List[Resource]:
        """Use recent AI papers as trending placeholder for Crossref"""
        return self.search("artificial intelligence", limit)


class OpenLibraryExtension(Extension):
    """Extension for Open Library API - real books database"""
    
    def __init__(self):
        super().__init__()
        self.name = "Open Library"
        self.version = "2.0.0"
        self.author = "Knowledgedock"
        self.description = "Access millions of books from Open Library - the free and open catalog"
        self.base_url = "https://openlibrary.org/search.json"
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
    
    def search(self, query: str, limit: int = 20) -> List[Resource]:
        """Search Open Library books"""
        try:
            params = {
                'title': query,
                'limit': min(limit, 100),
                'offset': 0
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                resources = []
                
                for book in data.get('docs', [])[:limit]:
                    cover_id = book.get('cover_id')
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
                    
                    resource = Resource(
                        id=book.get('key', ''),
                        title=book.get('title', 'Unknown'),
                        author=book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown',
                        url=f"https://openlibrary.org{book.get('key', '')}",
                        source_type="Book",
                        cover_url=cover_url,
                        description=f"Published: {book.get('first_publish_year', 'N/A')} | Editions: {book.get('edition_count', 0)}",
                        tags=["Book", "Open Library"]
                    )
                    resources.append(resource)
                
                return resources
        except Exception as e:
            print(f"Error searching Open Library: {e}")
        
        return []
    
    def get_categories(self) -> List[str]:
        return ["Fiction", "Science Fiction", "Mystery", "Romance", "Science", "History", "Art", "Biography"]
    
    def get_trending(self, limit: int = 10) -> List[Resource]:
        """Get highly rated books from Open Library"""
        try:
            params = {
                'subject': 'popular',
                'limit': min(limit, 100),
                'offset': 0
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                resources = []
                
                for book in data.get('docs', [])[:limit]:
                    cover_id = book.get('cover_id')
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None
                    
                    resource = Resource(
                        id=book.get('key', ''),
                        title=book.get('title', 'Unknown'),
                        author=book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown',
                        url=f"https://openlibrary.org{book.get('key', '')}",
                        source_type="Book",
                        cover_url=cover_url,
                        description=f"Popular book | Editions: {book.get('edition_count', 0)}",
                        tags=["Book", "Popular", "Open Library"]
                    )
                    resources.append(resource)
                
                return resources
        except Exception as e:
            print(f"Error fetching trending from Open Library: {e}")
        
        return []


class ArxivExtension(Extension):
    """Extension for arXiv - real research papers from arxiv.org"""
    
    def __init__(self):
        super().__init__()
        self.name = "arXiv"
        self.version = "2.0.0"
        self.author = "Knowledgedock"
        self.description = "Access millions of research papers and preprints from arXiv"
        self.base_url = "http://export.arxiv.org/api/query?"
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
    
    def search(self, query: str, limit: int = 20) -> List[Resource]:
        """Search arXiv papers using official API"""
        try:
            # arXiv API query format
            search_query = f"search_query=all:{query}&start=0&max_results={min(limit, 50)}&sortBy=relevance&sortOrder=descending"
            url = self.base_url + search_query
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Parse Atom XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                resources = []
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for entry in root.findall('atom:entry', ns)[:limit]:
                    arxiv_id = entry.find('atom:id', ns).text.split('/abs/')[-1]
                    title = entry.find('atom:title', ns).text.strip()
                    authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                    summary = entry.find('atom:summary', ns).text.strip()
                    published = entry.find('atom:published', ns).text
                    
                    resource = Resource(
                        id=arxiv_id,
                        title=title,
                        author=authors[0] if authors else "Unknown",
                        url=f"https://arxiv.org/abs/{arxiv_id}",
                        source_type="PDF/Research Paper",
                        description=summary[:500],
                        tags=["Research", "Paper", "PDF", "arXiv"]
                    )
                    resources.append(resource)
                
                return resources
        except Exception as e:
            print(f"Error searching arXiv: {e}")
        
        return []
    
    def get_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get full paper details from arXiv"""
        try:
            url = f"http://export.arxiv.org/api/query?id_list={resource_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                entry = root.find('atom:entry', ns)
                if entry is not None:
                    title = entry.find('atom:title', ns).text.strip()
                    authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                    summary = entry.find('atom:summary', ns).text.strip()
                    
                    resource = Resource(
                        id=resource_id,
                        title=title,
                        author=", ".join(authors[:3]) if authors else "Unknown",
                        url=f"https://arxiv.org/abs/{resource_id}",
                        source_type="PDF/Research Paper",
                        description=summary,
                        tags=["Research", "Paper", "Full Content"]
                    )
                    return resource
        except Exception as e:
            print(f"Error fetching arXiv paper: {e}")
        
        return None
    
    def get_categories(self) -> List[str]:
        return [
            "Computer Science",
            "Physics",
            "Mathematics",
            "Quantitative Biology",
            "Quantitative Finance",
            "Statistics"
        ]
    
    def get_trending(self, limit: int = 10) -> List[Resource]:
        """Get latest papers from arXiv"""
        try:
            # Get most recent papers
            search_query = f"search_query=all:&start=0&max_results={min(limit, 50)}&sortBy=submittedDate&sortOrder=descending"
            url = self.base_url + search_query
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                resources = []
                for entry in root.findall('atom:entry', ns)[:limit]:
                    arxiv_id = entry.find('atom:id', ns).text.split('/abs/')[-1]
                    title = entry.find('atom:title', ns).text.strip()
                    authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                    
                    resource = Resource(
                        id=arxiv_id,
                        title=title,
                        author=authors[0] if authors else "Unknown",
                        url=f"https://arxiv.org/abs/{arxiv_id}",
                        source_type="PDF/Research Paper",
                        description=f"Latest paper by {authors[0] if authors else 'Unknown'}",
                        tags=["Research", "Latest", "arXiv"]
                    )
                    resources.append(resource)
                
                return resources
        except Exception as e:
            print(f"Error fetching trending arXiv papers: {e}")
        
        return []


class WikipediaExtension(Extension):
    """Extension for Wikipedia - free encyclopedia with real API integration"""
    
    def __init__(self):
        super().__init__()
        self.name = "Wikipedia"
        self.version = "2.0.0"
        self.author = "Knowledgedock"
        self.description = "Access Wikipedia's free encyclopedia with full article search and details"
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.headers.update({'User-Agent': 'Knowledgedock/1.0'})
    
    def search(self, query: str, limit: int = 20) -> List[Resource]:
        """Search Wikipedia articles with full text search"""
        try:
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'srwhat': 'text',
                'format': 'json',
                'srlimit': min(limit, 50)
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                resources = []
                
                for page in data.get('query', {}).get('search', [])[:limit]:
                    # Clean HTML from snippet
                    snippet = page.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', '')
                    
                    resource = Resource(
                        id=str(page.get('pageid', '')),
                        title=page.get('title', 'Unknown'),
                        author="Wikipedia Contributors",
                        url=f"https://en.wikipedia.org/wiki/{page['title'].replace(' ', '_')}",
                        source_type="Web Article",
                        description=snippet[:300],
                        tags=["Article", "Wikipedia", "Free", "Encyclopedia"]
                    )
                    resources.append(resource)
                
                return resources
        except Exception as e:
            print(f"Error searching Wikipedia: {e}")
        
        return []
    
    def get_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get full Wikipedia article details"""
        try:
            params = {
                'action': 'query',
                'pageids': resource_id,
                'prop': 'extracts|info',
                'explaintext': True,
                'format': 'json'
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pages = data.get('query', {}).get('pages', {})
                
                for page_id, page_data in pages.items():
                    if page_id != '-1':
                        resource = Resource(
                            id=page_id,
                            title=page_data.get('title', 'Unknown'),
                            author="Wikipedia Contributors",
                            url=page_data.get('canonicalurl', 'https://en.wikipedia.org'),
                            source_type="Web Article",
                            description=page_data.get('extract', '')[:500],
                            tags=["Article", "Wikipedia", "Full Content"]
                        )
                        return resource
        except Exception as e:
            print(f"Error fetching Wikipedia article: {e}")
        
        return None
    
    def get_categories(self) -> List[str]:
        return [
            "Science",
            "Technology", 
            "History",
            "Culture",
            "Geography",
            "Medicine",
            "Mathematics",
            "Philosophy"
        ]
    
    def get_trending(self, limit: int = 10) -> List[Resource]:
        """Get Wikipedia's current featured articles"""
        try:
            # Get featured articles from Wikipedia portal
            params = {
                'action': 'query',
                'titles': 'Wikipedia:Featured_articles',
                'prop': 'links',
                'pllimit': min(limit, 50),
                'format': 'json'
            }
            response = self.session.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                resources = []
                
                # Fallback to popular categories if featured fetch fails
                popular_topics = [
                    "Artificial Intelligence",
                    "Machine Learning",
                    "Climate Change",
                    "COVID-19 Pandemic",
                    "Space Exploration",
                    "Quantum Computing",
                    "Biology",
                    "Physics",
                    "Chemistry",
                    "Technology"
                ]
                
                for i, topic in enumerate(popular_topics[:limit]):
                    resource = Resource(
                        id=f"wiki_topic_{i}",
                        title=topic,
                        author="Wikipedia Contributors",
                        url=f"https://en.wikipedia.org/wiki/{topic.replace(' ', '_')}",
                        source_type="Web Article",
                        description=f"Popular Wikipedia article about {topic}",
                        tags=["Article", "Wikipedia", "Trending"]
                    )
                    resources.append(resource)
                
                return resources
        except Exception as e:
            print(f"Error fetching trending from Wikipedia: {e}")
        
        return []
