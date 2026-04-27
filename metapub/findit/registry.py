"""Journal Registry - Database-backed journal and publisher management for FindIt.

This module replaces the static journal lists with a SQLite-backed registry system
that can efficiently handle thousands of journals with lazy loading and caching.
"""

import sqlite3
import logging
import os
import json
import re
import yaml
from typing import Optional, Dict, Tuple, List
from ..config import DEFAULT_CACHE_DIR
from ..cache_utils import get_cache_path

log = logging.getLogger('metapub.findit.registry')

REGISTRY_DB_FILENAME = 'journal_registry.db'

class JournalRegistry:
    """Database-backed journal registry with lazy loading and caching."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the journal registry.
        
        Args:
            db_path: Path to the SQLite database. If None, uses shipped database.
        """
        if db_path is None:
            # Use shipped registry database by default
            shipped_db_path = os.path.join(os.path.dirname(__file__), 'data', 'registry.db')
            if os.path.exists(shipped_db_path):
                db_path = shipped_db_path
                log.debug(f"Using shipped registry database: {db_path}")
            else:
                # Fallback to cache directory for development/migration
                db_path = get_cache_path(DEFAULT_CACHE_DIR, REGISTRY_DB_FILENAME)
                log.warning(f"Shipped registry not found, using cache: {db_path}")
        
        self.db_path = db_path
        self._conn = None
        self._ensure_database()
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection, creating if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def _ensure_database(self):
        """Create database tables if they don't exist and auto-populate if empty."""
        pass
    
    def _add_missing_columns(self, conn: sqlite3.Connection):
        """Add missing columns to existing tables for backward compatibility."""
        pass
    
    def _is_using_shipped_database(self) -> bool:
        """Check if we're using the shipped registry database."""
        pass
    
    def _auto_populate_if_empty(self):
        """Auto-populate database from embedded journal modules if empty.
        
        This ensures that PyPI-installed packages work out of the box without
        requiring users to manually run migration scripts.
        """
        pass
                # Don't raise - allow system to continue with empty database
                # Users can still manually run migration if needed
    
    def _populate_from_embedded_modules(self):
        """Populate database from the embedded journal module data.
        
        This is a simplified version of the migration script that runs
        automatically when the database is empty.
        """
        pass
    
    def get_publisher_for_journal(self, journal_name: str) -> Optional[Dict]:
        """Get publisher information for a journal name.
        
        Args:
            journal_name: The journal name or abbreviation to look up.
            
        Returns:
            Dictionary with publisher info (name, dance_function, format_template) or None.
        """
        conn = self._get_connection()
        
        # First try direct journal name match (case-insensitive)
        cursor = conn.execute('''
            SELECT p.name, p.dance_function, p.format_template, p.base_url, p.config_data, 
                   j.format_params, j.aliases, j.notes
            FROM journals j
            JOIN publishers p ON j.publisher_id = p.id
            WHERE LOWER(j.name) = LOWER(?) AND j.is_active = 1 AND p.is_active = 1
        ''', (journal_name,))
        
        result = cursor.fetchone()
        if result:
            return dict(result)
        
        # Try alias match - check if journal_name is in the aliases JSON array
        cursor = conn.execute('''
            SELECT p.name, p.dance_function, p.format_template, p.base_url, p.config_data,
                   j.format_params, j.aliases, j.notes
            FROM journals j
            JOIN publishers p ON j.publisher_id = p.id
            WHERE j.aliases IS NOT NULL AND j.is_active = 1 AND p.is_active = 1
        ''')
        
        for row in cursor.fetchall():
            try:
                aliases = json.loads(row['aliases'])
                # Case-insensitive alias matching
                if any(alias.lower() == journal_name.lower() for alias in aliases):
                    return dict(row)
            except (json.JSONDecodeError, TypeError):
                continue
        
        return None
    
    def get_publisher_config(self, publisher_name: str) -> Optional[Dict]:
        """Get detailed publisher configuration including JSON config data.
        
        Args:
            publisher_name: Name of the publisher
            
        Returns:
            Dictionary with full publisher config or None
        """
        conn = self._get_connection()
        cursor = conn.execute('''
            SELECT name, dance_function, format_template, base_url, config_data, notes, is_active
            FROM publishers
            WHERE name = ? AND is_active = 1
        ''', (publisher_name,))
        
        result = cursor.fetchone()
        if result:
            config = dict(result)
            # Parse JSON config_data if present
            if config['config_data']:
                try:
                    config['config_data'] = json.loads(config['config_data'])
                except (json.JSONDecodeError, TypeError):
                    config['config_data'] = None
            return config
        return None
    
    def add_publisher(self, name: str, dance_function: str, 
                     format_template: str = None, base_url: str = None,
                     config_data: str = None, notes: str = None, 
                     is_active: bool = True) -> int:
        """Add a new publisher to the registry.
        
        Args:
            name: Publisher name
            dance_function: Name of the dance function to call
            format_template: URL format template (optional)
            base_url: Base URL for the publisher (optional)
            config_data: JSON string for complex configuration (optional)
            notes: Migration notes/documentation (optional)
            is_active: Enable/disable publisher (default True)
            
        Returns:
            Publisher ID
        """
        conn = self._get_connection()
        cursor = conn.execute('''
            INSERT OR REPLACE INTO publishers (name, dance_function, format_template, base_url, config_data, notes, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, dance_function, format_template, base_url, config_data, notes, is_active))
        conn.commit()
        return cursor.lastrowid
    
    def add_journal(self, name: str, publisher_id: int, 
                   format_params: str = None, aliases: List[str] = None,
                   is_active: bool = True, notes: str = None) -> int:
        """Add a new journal to the registry.
        
        Args:
            name: Journal name/abbreviation
            publisher_id: ID of the publisher
            format_params: JSON string of format parameters (optional)
            aliases: List of alternate names for this journal (optional)
            is_active: Enable/disable journal (default True)
            notes: Special handling notes (optional)
            
        Returns:
            Journal ID
        """
        conn = self._get_connection()
        
        # Convert aliases list to JSON string
        aliases_json = None
        if aliases:
                aliases_json = json.dumps(aliases)
        
        # Insert journal
        cursor = conn.execute('''
            INSERT OR REPLACE INTO journals (name, publisher_id, format_params, aliases, is_active, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, publisher_id, format_params, aliases_json, is_active, notes))
        journal_id = cursor.lastrowid
        
        conn.commit()
        return journal_id
    
    def get_all_journals(self) -> List[str]:
        """Get all journal names in the registry."""
        pass
    
    def get_journal_params(self, journal_name: str) -> Optional[Dict]:
        """Get format parameters for a specific journal.
        
        Args:
            journal_name: The journal name or abbreviation to look up.
            
        Returns:
            Dictionary with journal format parameters or None.
        """
        
        conn = self._get_connection()
        
        # Find journal matches, prioritizing entries with format_params
        cursor = conn.execute('''
            SELECT format_params
            FROM journals
            WHERE name = ? AND is_active = 1
            ORDER BY CASE WHEN format_params IS NOT NULL THEN 0 ELSE 1 END
        ''', (journal_name,))
        
        result = cursor.fetchone()
        if result and result[0]:
            try:
                return json.loads(result[0])
            except (json.JSONDecodeError, TypeError):
                return None
                
        return None
    
    def get_publisher_by_url_pattern(self, url: str) -> Optional[Dict]:
        """Find publisher by matching URL pattern.
        
        Args:
            url: URL to match against publisher templates
            
        Returns:
            Dictionary with publisher info or None if no match found
        """
        pass
    
    def _url_matches_template(self, url: str, template: str) -> bool:
        """Check if URL matches a template pattern.
        
        Args:
            url: Actual URL to check
            template: Template with placeholders like {doi}, {host}, etc.
            
        Returns:
            True if URL matches template pattern
        """
        pass

    def get_stats(self) -> Dict[str, int]:
        """Get registry statistics."""
        pass
    
    def close(self):
        """Close database connection."""
        if hasattr(self, '_conn') and self._conn:
            self._conn.close()
            self._conn = None
    
    def get_yaml_config(self, publisher_id: str) -> Optional[Dict]:
        """Load YAML configuration for a publisher.
        
        Args:
            publisher_id: Publisher ID (matches YAML filename)
            
        Returns:
            Dictionary with YAML configuration or None if not found
        """
        yaml_path = os.path.join(os.path.dirname(__file__), 'journals', f'{publisher_id}.yaml')
        
        if not os.path.exists(yaml_path):
            log.debug(f"YAML config not found: {yaml_path}")
            return None
            
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except (yaml.YAMLError, IOError) as error:
            log.error(f"Error loading YAML config {yaml_path}: {error}")
            return None
    
    def get_url_templates(self, publisher_id: str) -> Dict[str, List[Dict]]:
        """Get URL templates for a publisher from YAML configuration.
        
        Args:
            publisher_id: Publisher ID
            
        Returns:
            Dictionary with 'primary', 'secondary', and 'legacy' template lists
        """
        config = self.get_yaml_config(publisher_id)
        if not config or 'url_patterns' not in config:
            return {'primary': [], 'secondary': [], 'legacy': []}
        
        url_patterns = config['url_patterns']
        templates = {'primary': [], 'secondary': [], 'legacy': []}
        
        # Primary template
        if 'primary_template' in url_patterns:
            templates['primary'].append({
                'template': url_patterns['primary_template'],
                'description': 'Primary URL template',
                'priority': 0
            })
        
        # Secondary templates
        if 'secondary_templates' in url_patterns:
            templates['secondary'] = url_patterns['secondary_templates']
        
        # Legacy templates
        if 'legacy_templates' in url_patterns:
            templates['legacy'] = url_patterns['legacy_templates']
            
        return templates
    
    def get_journal_parameters(self, publisher_id: str, journal_name: str) -> Optional[Dict]:
        """Get journal-specific parameters from YAML configuration.
        
        Args:
            publisher_id: Publisher ID
            journal_name: Journal name to look up
            
        Returns:
            Dictionary with journal parameters or None
        """
        config = self.get_yaml_config(publisher_id)
        if not config or 'journals' not in config:
            return None
        
        journals = config['journals']
        
        # Check parameterized journals
        if 'parameterized' in journals and journal_name in journals['parameterized']:
            return journals['parameterized'][journal_name]
        
        # For simple_list journals, return empty dict (no special parameters)
        if 'simple_list' in journals and journal_name in journals['simple_list']:
            return {}
            
        return None

    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, '_conn'):
            self.close()


def standardize_journal_name(journal_name: str) -> str:
    """Standardize journal name for consistent lookups.
    
    This function normalizes journal names by:
    - Stripping whitespace
    - Converting common abbreviations
    - Handling special cases
    
    Args:
        journal_name: Raw journal name from PubMed
        
    Returns:
        Standardized journal name
    """
    if not journal_name:
        return journal_name
    
    # Basic cleanup
    name = journal_name.strip()
    
    # Handle common PubMed variations
    # Add more normalizations as needed
    replacements = {
        'J.': 'J',
        'Am.': 'Am',
        'Br.': 'Br',
        'Int.': 'Int',
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    return name