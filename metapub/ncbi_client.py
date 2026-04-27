"""
Lightweight NCBI E-utilities client - replacement for eutils library.
Provides direct HTTP interface to NCBI APIs with rate limiting and caching.
"""

import time
import sqlite3
import hashlib
import logging
import requests
from threading import Lock
from urllib.parse import urlencode
from typing import Dict, List, Optional, Union

from .exceptions import MetaPubError
from .ncbi_errors import diagnose_ncbi_error, NCBIServiceError

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

log = logging.getLogger('metapub.ncbi_client')


class RateLimiter:
    """Thread-safe rate limiter to respect NCBI API limits.
    
    NCBI E-utilities enforces rate limits:
    - 3 requests per second without API key
    - 10 requests per second with API key
    
    This rate limiter ensures compliance by enforcing minimum intervals
    between requests using thread-safe locking.
    
    Args:
        requests_per_second (int): Maximum requests allowed per second. 
            Defaults to 10 (assumes API key usage).
    
    Attributes:
        requests_per_second (int): Configured rate limit
        min_interval (float): Minimum time between requests in seconds
        last_request_time (float): Timestamp of last request
        lock (threading.Lock): Thread synchronization lock
    """
    
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = Lock()
    
    def wait_if_needed(self):
        """Block execution if minimum interval hasn't elapsed since last request.
        
        Thread-safe method that enforces rate limiting by sleeping if needed.
        Updates last_request_time after any required wait period.
        
        Returns:
            None
        """
        pass


class SimpleCache:
    """Thread-safe SQLite-based cache for NCBI API responses.
    
    This cache provides persistent storage for API responses to reduce
    network requests and improve performance. It maintains compatibility
    with existing metapub cache files and provides both URL-based caching
    and dictionary-style access patterns.
    
    The cache stores responses with timestamps but does not implement TTL
    expiration - responses are cached indefinitely unless manually cleared.
    
    Features:
    - Thread-safe operations using locks
    - Automatic database initialization
    - Compatible with existing cache schema
    - Supports both binary and text data
    - JSON serialization for complex objects
    - Dictionary-style access (__getitem__, __setitem__, __contains__)
    
    Args:
        cache_path (str): Path to SQLite database file for cache storage
    
    Attributes:
        cache_path (str): Path to the SQLite database
        lock (threading.Lock): Thread synchronization lock
    """
    
    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        self.lock = Lock()
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with cache table.
        
        Creates the cache table if it doesn't exist, using a schema
        compatible with existing cache files.
        
        Table schema:
        - key: BLOB PRIMARY KEY - Cache key (URL + parameters)  
        - value: BLOB - Cached response data
        - created: INTEGER - Unix timestamp of cache entry
        - value_compressed: BOOL - Whether value is compressed (legacy field)
        """
        pass
    
    def _make_key(self, url: str, params: Dict) -> bytes:
        """Generate deterministic cache key from URL and parameters.
        
        Creates a reproducible cache key by combining the URL with sorted
        parameters. This ensures that requests with identical parameters
        (regardless of order) use the same cache entry.
        
        Args:
            url (str): Base URL for the request
            params (Dict): Request parameters dictionary
            
        Returns:
            bytes: UTF-8 encoded cache key
        """
        sorted_params = sorted(params.items())
        key_string = f"{url}?{urlencode(sorted_params)}"
        return key_string.encode()
    
    def get(self, url: str, params: Dict) -> Optional[str]:
        """Retrieve cached response for URL and parameters.
        
        Thread-safe method to fetch cached API responses. Returns None
        if no cached response is found.
        
        Args:
            url (str): Base URL that was cached
            params (Dict): Request parameters used for the cached request
            
        Returns:
            Optional[str]: Cached response as string, or None if not found
        """
        with self.lock:
            key = self._make_key(url, params)
            
            with sqlite3.connect(self.cache_path) as conn:
                result = conn.execute(
                    "SELECT value FROM cache WHERE key = ?",
                    (key,)
                ).fetchone()
                
                if result:
                    value = result[0]
                    if isinstance(value, bytes):
                        return value.decode('utf-8')
                    return str(value)
                
                return None
    
    def set(self, url: str, params: Dict, value: str):
        """Store API response in cache.
        
        Thread-safe method to cache API responses with current timestamp.
        Uses INSERT OR REPLACE to handle both new entries and updates.
        
        Args:
            url (str): Base URL to cache
            params (Dict): Request parameters for the cached request  
            value (str): API response content to cache
            
        Returns:
            None
        """
        pass
    
    def __getitem__(self, key):
        """Dictionary-style access for compatibility."""
        with self.lock:
            # Handle both string keys and byte keys
            if isinstance(key, str):
                key = key.encode('utf-8')
                
            with sqlite3.connect(self.cache_path) as conn:
                result = conn.execute(
                    "SELECT value FROM cache WHERE key = ?",
                    (key,)
                ).fetchone()
                
                if result:
                    value = result[0]
                    if isinstance(value, bytes):
                        value = value.decode('utf-8')
                    else:
                        value = str(value)
                    
                    # Try to deserialize as JSON for findit compatibility
                    try:
                        import json
                        return json.loads(value)
                    except (json.JSONDecodeError, ValueError):
                        # If not JSON, return as string
                        return value
                else:
                    raise KeyError(key)
    
    def __setitem__(self, key, value):
        """Dictionary-style setting for compatibility."""
        with self.lock:
            # Handle both string keys and byte keys
            if isinstance(key, str):
                key = key.encode('utf-8')
            
            now = int(time.time())
            
            with sqlite3.connect(self.cache_path) as conn:
                # Handle different value types (string, dict, etc.)
                if isinstance(value, str):
                    stored_value = value.encode('utf-8')
                else:
                    # For complex objects, store as string representation
                    import json
                    stored_value = json.dumps(value).encode('utf-8')
                
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, created, value_compressed) VALUES (?, ?, ?, ?)",
                    (key, stored_value, now, 0)
                )
    
    def __contains__(self, key):
        """Dictionary-style 'in' operator for compatibility."""
        try:
            self[key]
            return True
        except KeyError:
            return False


class NCBIClient:
    """Lightweight NCBI E-utilities client with caching and rate limiting.
    
    This client provides a modern interface to NCBI APIs with:
    - Automatic rate limiting respecting NCBI guidelines
    - Persistent SQLite-based response caching
    - Comprehensive error handling and diagnostics
    - Support for all major E-utilities endpoints
    - API key support for higher rate limits
    
    The client automatically detects API key usage and adjusts rate limiting
    accordingly (3 req/sec without key, 10 req/sec with key).
    
    Args:
        api_key (Optional[str]): NCBI API key for higher rate limits
        cache_path (Optional[str]): Path to SQLite cache file. If None, no caching
        requests_per_second (int): Maximum requests per second (capped by NCBI limits)
        tool (str): Tool identifier for NCBI logging
        email (str): Email address for NCBI contact (recommended)
    
    Attributes:
        BASE_URL (str): Base URL for NCBI E-utilities
        api_key (Optional[str]): Configured API key
        tool (str): Tool identifier
        email (str): Contact email
        rate_limiter (RateLimiter): Rate limiting handler
        cache (Optional[SimpleCache]): Response cache if enabled
        session (requests.Session): HTTP session for requests
    """
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, api_key: Optional[str] = None, cache_path: Optional[str] = None, 
                 requests_per_second: int = 10, tool: str = "metapub", email: str = ""):
        self.api_key = api_key
        self.tool = tool
        self.email = email
        
        # Setup rate limiting
        rps = 10 if api_key else 3  # NCBI limits: 10/sec with key, 3/sec without
        self.rate_limiter = RateLimiter(min(requests_per_second, rps))
        
        # Setup caching
        self.cache = SimpleCache(cache_path) if cache_path else None
        
        # Setup HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'{tool}/metapub-ncbi-client'
        })
    
    def _build_params(self, **kwargs) -> Dict[str, str]:
        """Build standard parameters for NCBI requests."""
        pass
    
    def _is_valid_xml_response(self, content: str, response: requests.Response) -> bool:
        """Validate that response content is actually XML, not HTML error pages."""
        pass
    
    def _make_request(self, endpoint: str, **params) -> str:
        """Make HTTP request to NCBI with caching and rate limiting."""
        pass
    
    def efetch(self, db: str, id: Union[str, List[str]], rettype: str = 'xml', 
               retmode: str = 'text', **kwargs) -> str:
        """Fetch full records for given IDs."""
        pass
    
    def esearch(self, db: str, term: str, retmax: int = 20, retstart: int = 0,
                sort: str = None, **kwargs) -> str:
        """Search database and return UIDs."""
        pass
    
    def elink(self, dbfrom: str, id: Union[str, List[str]], db: str = None,
              cmd: str = 'neighbor', **kwargs) -> str:
        """Find related records."""
        pass
    
    def esummary(self, db: str, id: Union[str, List[str]], retmode: str = 'xml',
                 **kwargs) -> str:
        """Get document summaries."""
        pass
    
    def einfo(self, db: str = None, **kwargs) -> str:
        """Get database information."""
        pass
