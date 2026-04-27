"""
Compatibility layer that mimics the eutils library interface.
Provides drop-in replacement using NCBIClient with proper caching (no eutils dependency).
(This is a transitional step en route to metapub 1.0.)
"""

import logging
from .ncbi_client import NCBIClient
from .exceptions import MetaPubError

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

log = logging.getLogger('metapub.eutils_compat')


class EutilsRequestError(Exception):
    """Compatibility exception to match eutils library."""
    pass


class QueryService:
    """Drop-in replacement for eutils.QueryService."""

    def __init__(self, cache=None, api_key=None, email="", tool="metapub"):
        # Use NCBIClient with built-in caching
        self.client = NCBIClient(
            api_key=api_key,
            cache_path=cache,
            email=email,
            tool=tool
        )
        # Expose cache for compatibility with tests
        self._cache = self.client.cache

    def _is_valid_xml_response(self, content: str) -> bool:
        """Validate that response content is actually XML, not HTML error pages."""
        pass

    def efetch(self, params: dict) -> str:
        """Compatibility method for efetch."""
        pass

    def esearch(self, params: dict) -> str:
        """Compatibility method for esearch."""
        pass

    def elink(self, params: dict) -> str:
        """Compatibility method for elink."""
        pass

    def esummary(self, params: dict) -> str:
        """Compatibility method for esummary."""
        pass

    def einfo(self, params: dict = None) -> str:
        """Compatibility method for einfo."""
        pass
