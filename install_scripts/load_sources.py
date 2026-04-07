#!/usr/bin/python3
"""
Centralized source configuration loader for TELE-Vir.

Provides easy access to all download sources organized by category:
- databases: Kraken2, Kaiju, UniRef, SILVA, etc.
- software: Git repos, archive downloads
- host_genomes: NCBI RefSeq host genome locations
- infrastructure: Conda, tools, NCBI E-utilities

Usage:
    from load_sources import sources, get_db_url, get_host_config
    
    # Get a full section
    kraken2_dbs = sources['databases']['kraken2']
    
    # Get specific URL
    viral_db = get_db_url('kraken2', 'viral')
    
    # Get host genome config
    human = get_host_config('homo_sapiens')
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Union

try:
    import yaml
    Loader = yaml.CLoader if hasattr(yaml, 'CLoader') else yaml.Loader
    Dumper = yaml.CDumper if hasattr(yaml, 'CDumper') else yaml.Dumper
except ImportError:
    import yaml
    Loader = yaml.Loader
    Dumper = yaml.Dumper


class SourceLoader:
    """Centralized source configuration loader."""
    
    _instance = None
    _sources = None
    _config_path = None
    
    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        if self._initialized and self._sources is not None:
            return
            
        if config_path is None:
            config_path = self._find_config_path()
        
        self._config_path = config_path
        self._load_sources()
        self._initialized = True
    
    def _find_config_path(self) -> str:
        """Find sources.yaml in common locations."""
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'sources.yaml'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sources.yaml'),
            os.path.join(os.getcwd(), 'sources.yaml'),
            '/opt/televir/sources.yaml',
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return possible_paths[0]
    
    def _load_sources(self):
        """Load sources from YAML file."""
        try:
            with open(self._config_path, 'r') as f:
                self._sources = yaml.load(f, Loader=Loader)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Configuration file not found at: {self._config_path}\n"
                f"Please ensure sources.yaml exists in the project root or install_scripts directory."
            )
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing sources.yaml: {e}")
    
    @property
    def sources(self) -> Dict[str, Any]:
        """Get all sources."""
        return self._sources
    
    @property
    def version(self) -> str:
        """Get config version."""
        return self._sources.get('version', 'unknown')
    
    @property
    def last_updated(self) -> str:
        """Get last update date."""
        return self._sources.get('last_updated', 'unknown')
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get nested value from sources."""
        value = self._sources
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def get_refseq_entry(self, organism: str, db_type: str) -> Optional[Dict]:
        """Get RefSeq entry for specific organism and type (protein/genome).
        
        Args:
            organism: 'viral' or 'bacterial'
            db_type: 'protein' or 'genome'
            
        Returns:
            Dict with url, description, file_pattern or None
        """
        key = f"{organism}_{db_type}"
        return self.get('databases', 'refseq', key)
    
    def get_db_url(self, category: str, name: str) -> Optional[str]:
        """Get database URL by category and name.
        
        Args:
            category: Database category (e.g., 'kraken2', 'kaiju', 'protein')
            name: Database name within category (e.g., 'viral', 'uniref90')
            
        Returns:
            URL string or None if not found
        """
        db_section = self._sources.get('databases', {}).get(category, {})
        if isinstance(db_section, dict):
            db_entry = db_section.get(name, {})
            if isinstance(db_entry, dict):
                return db_entry.get('url')
        return None
    
    def get_db_version(self, category: str, name: str) -> Optional[str]:
        """Get database version from sources.yaml.
        
        First checks 'version' field, then extracts from 'file' or 'url' string.
        
        Args:
            category: Database category (e.g., 'kraken2', 'kaiju', 'metaphlan')
            name: Database name within category
            
        Returns:
            Version string or None if not found
        """
        entry = self.get_db_entry(category, name)
        if not entry:
            return None
        
        version = entry.get('version')
        if version:
            return version
        
        file_str = entry.get('file', '') or entry.get('url', '')
        return self.extract_version_from_string(file_str)
    
    def get_db_entry(self, category: str, name: str) -> Optional[Dict]:
        """Get full database entry from sources.yaml.
        
        Args:
            category: Database category
            name: Database name
            
        Returns:
            Dict with url, version, file, description or None if not found
        """
        db_section = self._sources.get('databases', {}).get(category, {})
        if isinstance(db_section, dict):
            entry = db_section.get(name, {})
            if entry and isinstance(entry, dict):
                return entry
        return None
    
    def is_db_enabled(self, category: str, name: str) -> bool:
        """Check if a database is enabled for installation.
        
        Args:
            category: Database category (e.g., 'kraken2', 'kaiju', 'protein')
            name: Database name within category
            
        Returns:
            True if install is true/empty/missing, False if install is explicitly false
        """
        entry = self.get_db_entry(category, name)
        if entry is None:
            return False
        
        install_val = entry.get('install')
        if install_val is None:
            return True
        return bool(install_val)
    
    def get_install_types(self, category: str, name: str) -> list:
        """Get list of install types for a database.
        
        Args:
            category: Database category
            name: Database name
            
        Returns:
            List of install types (e.g., ['filter'], ['prot', 'nuc'])
        """
        entry = self.get_db_entry(category, name)
        if entry is None:
            return []
        
        return entry.get('install_types', [])
    
    def get_db_key(self, category: str, name: str) -> str:
        """Get db_key for a database.
        
        Args:
            category: Database category
            name: Database name
            
        Returns:
            db_key string (filter, prot, nuc) - inferred from install_types if not explicit
        """
        entry = self.get_db_entry(category, name)
        if entry is None:
            return ""
        
        # Return explicit db_key if set
        db_key = entry.get('db_key')
        if db_key:
            return db_key
        
        # Infer from install_types
        install_types = entry.get('install_types', [])
        if 'filter' in install_types:
            return 'filter'
        if 'prot' in install_types:
            return 'prot'
        if 'nuc' in install_types:
            return 'nuc'
        if 'host' in install_types:
            return 'host'
        
        return ""
    
    def get_download_method(self, category: str, name: str) -> str:
        """Get download method for a database.
        
        Args:
            category: Database category
            name: Database name
            
        Returns:
            Download method: 'filter', 'refseq', 'refseq_prot', 'refseq_gen'
        """
        entry = self.get_db_entry(category, name)
        if entry is None:
            return 'filter'
        
        # Check for explicit download_method
        method = entry.get('download_method')
        if method:
            return method
        
        # For refseq, determine based on refseq_type
        if category == 'refseq':
            refseq_type = entry.get('refseq_type', 'protein')
            return f'refseq_{refseq_type}'
        
        # Default based on db_key or install_types
        db_key = self.get_db_key(category, name)
        if db_key in ['prot', 'nuc', 'filter']:
            return 'filter'
        
        return 'filter'
    
    def list_enabled_databases(self, category: str) -> list:
        """List enabled databases for a category.
        
        Args:
            category: Database category (e.g., 'ribosomal_rna', 'protein')
            
        Returns:
            List of (db_name, entry) tuples for enabled databases
        """
        db_section = self._sources.get('databases', {}).get(category, {})
        if not isinstance(db_section, dict):
            return []
        
        result = []
        for db_name, entry in db_section.items():
            if isinstance(entry, dict) and self.is_db_enabled(category, db_name):
                result.append((db_name, entry))
        
        return result
    
    def list_all_db_configs(self, categories: list) -> dict:
        """Get download configuration for multiple categories.
        
        Args:
            categories: List of categories to process
            
        Returns:
            Dict mapping category -> list of (db_name, db_key, download_method)
        """
        result = {}
        for category in categories:
            db_configs = []
            for db_name, entry in self.list_enabled_databases(category):
                db_key = self.get_db_key(category, db_name)
                download_method = self.get_download_method(category, db_name)
                
                # For refseq, also get organism/type for get_refseq_entry
                refseq_organism = entry.get('refseq_organism')
                refseq_type = entry.get('refseq_type')
                
                db_configs.append({
                    'name': db_name,
                    'db_key': db_key,
                    'download_method': download_method,
                    'entry': entry,
                    'refseq_organism': refseq_organism,
                    'refseq_type': refseq_type,
                })
            result[category] = db_configs
        
        return result
    
    def get_prebuilt_index_path(self, tool: str, dbname: str) -> Optional[str]:
        """Get prebuilt index path from sources.yaml.
        
        Args:
            tool: 'centrifuge' or 'kraken2'
            dbname: Database name (e.g., 'viral', 'bacteria', 'eupathdb46')
            
        Returns:
            Path string or None if not configured
        """
        return self.get('databases', 'prebuilt_indices', tool, dbname, 'path')
    
    def extract_version_from_string(self, s: str) -> Optional[str]:
        """Extract version from filename or URL string (case-insensitive).
        
        Patterns tried:
            _YYYYMMDD or _YYYYMMDD. -> 20250402
            YYYY-MM-DD -> 2024-08-15
            vYYYYxN -> vJan25
            
        Args:
            s: String to extract version from (filename or URL)
            
        Returns:
            Extracted version string or None
        """
        import re
        if not s:
            return None
        
        s_lower = s.lower()
        patterns = [
            (r'_(\d{8})(?:\.|_|$)', 1),  # _20250402. or _20250402_ or _20250402end
            (r'_(\d{6})(?:\.|_|$)', 1),  # _202504. or _202504_ or _202504end
            (r'\.(\d{8})\.', 1),    # .20250402.
            (r'(\d{4}-\d{2}-\d{2})', 1),  # 2024-08-15
            (r'_v([a-z]+\d{4})', 1),  # _vJan25 (month prefix)
            (r'(\d{8})(?:\.|_|$)', 1),  # 20250402. or 20250402_ or 20250402end
        ]
        
        for pattern, group in patterns:
            match = re.search(pattern, s_lower)
            if match:
                return match.group(1)
        return None
    
    def get_host_config(self, host_key: str) -> Optional[Dict[str, str]]:
        """Get host genome configuration.
        
        Args:
            host_key: Host identifier (e.g., 'homo_sapiens', 'hg38')
            
        Returns:
            Dict with host_name, common_name, host, path, file or None
        """
        hosts = self._sources.get('host_genomes', {})
        
        if host_key in hosts:
            config = hosts[host_key]
            if isinstance(config, dict):
                return config
            return None
        
        for host_data in hosts.values():
            if isinstance(host_data, dict):
                if host_data.get('host_name') == host_key or host_data.get('common_name') == host_key:
                    return host_data
        
        return None
    
    def get_software_url(self, name: str, repo_type: str = 'archives') -> Optional[str]:
        """Get software download URL.
        
        Args:
            name: Software name (e.g., 'clark', 'fastqc')
            repo_type: 'archives' or 'git_repos'
            
        Returns:
            URL string or None if not found
        """
        software = self._sources.get('software', {}).get(repo_type, {})
        if isinstance(software, dict):
            entry = software.get(name, {})
            if isinstance(entry, dict):
                return entry.get('url')
        return None
    
    def get_git_url(self, name: str) -> Optional[str]:
        """Get Git repository URL."""
        return self.get_software_url(name, 'git_repos')
    
    def get_infrastructure_url(self, category: str, name: str) -> Optional[str]:
        """Get infrastructure tool URL."""
        infra = self._sources.get('infrastructure', {}).get(category, {})
        if isinstance(infra, dict):
            entry = infra.get(name, {})
            if isinstance(entry, dict):
                return entry.get('url')
        return None
    
    def get_ncbi_eutils_url(self, endpoint: str) -> Optional[str]:
        """Get NCBI E-utilities endpoint URL."""
        return self.get_infrastructure_url('ncbi_eutils', endpoint)
    
    def list_databases(self, category: Optional[str] = None) -> Union[Dict, Dict[str, Dict]]:
        """List available databases.
        
        Args:
            category: Optional specific category to list
            
        Returns:
            Dict of databases with their metadata
        """
        dbs = self._sources.get('databases', {})
        if category:
            return dbs.get(category, {})
        return dbs
    
    def list_hosts(self) -> Dict[str, Dict]:
        """List all available host genomes."""
        return self._sources.get('host_genomes', {})
    
    def list_software(self) -> Dict[str, Dict]:
        """List all available software."""
        return self._sources.get('software', {})


_loader = None

def get_loader(config_path: Optional[str] = None) -> SourceLoader:
    """Get singleton SourceLoader instance."""
    global _loader
    if _loader is None:
        _loader = SourceLoader(config_path)
    return _loader


def reload(config_path: Optional[str] = None):
    """Reload configuration from file."""
    global _loader
    _loader = SourceLoader(config_path)
    return _loader


def sources() -> Dict[str, Any]:
    """Get all sources (convenience accessor)."""
    return get_loader().sources


def version() -> str:
    """Get config version."""
    return get_loader().version


def last_updated() -> str:
    """Get last update date."""
    return get_loader().last_updated


def get(*keys: str, default: Any = None) -> Any:
    """Get nested value from sources."""
    return get_loader().get(*keys, default=default)

def get_db_url(category: str, name: str) -> Optional[str]:
    """Get database URL."""
    return get_loader().get_db_url(category, name)

def get_db_version(category: str, name: str) -> Optional[str]:
    """Get database version from sources.yaml.
    
    First checks 'version' field, then extracts from 'file' or 'url' string.
    """
    return get_loader().get_db_version(category, name)

def get_db_entry(category: str, name: str) -> Optional[Dict]:
    """Get full database entry from sources.yaml."""
    return get_loader().get_db_entry(category, name)

def is_db_enabled(category: str, name: str) -> bool:
    """Check if a database is enabled for installation.
    
    Returns True if install is true/empty/missing, False if install is explicitly false.
    """
    return get_loader().is_db_enabled(category, name)

def get_install_types(category: str, name: str) -> list:
    """Get list of install types for a database.
    
    Returns list of install types (e.g., ['filter'], ['prot', 'nuc']).
    """
    return get_loader().get_install_types(category, name)

def get_db_key(category: str, name: str) -> str:
    """Get db_key for a database.
    
    Returns db_key string (filter, prot, nuc) - inferred from install_types if not explicit.
    """
    return get_loader().get_db_key(category, name)

def get_download_method(category: str, name: str) -> str:
    """Get download method for a database.
    
    Returns: 'filter', 'refseq', 'refseq_prot', 'refseq_gen'.
    """
    return get_loader().get_download_method(category, name)

def list_enabled_databases(category: str) -> list:
    """List enabled databases for a category.
    
    Returns list of (db_name, entry) tuples for enabled databases.
    """
    return get_loader().list_enabled_databases(category)

def list_all_db_configs(categories: list) -> dict:
    """Get download configuration for multiple categories.
    
    Returns dict mapping category -> list of config dicts.
    """
    return get_loader().list_all_db_configs(categories)

def get_refseq_entry(organism: str, db_type: str) -> Optional[Dict]:
    """Get RefSeq entry for specific organism and type (protein/genome).
    
    Args:
        organism: 'viral' or 'bacterial'
        db_type: 'protein' or 'genome'
        
    Returns:
        Dict with url, description, file_pattern or None
    """
    return get_loader().get_refseq_entry(organism, db_type)

def get_prebuilt_index_path(tool: str, dbname: str) -> Optional[str]:
    """Get prebuilt index path from sources.yaml.
    
    Args:
        tool: 'centrifuge' or 'kraken2'
        dbname: Database name (e.g., 'viral', 'bacteria', 'eupathdb46')
        
    Returns:
        Path string or None if not configured
    """
    return get_loader().get_prebuilt_index_path(tool, dbname)

def extract_version_from_string(s: str) -> Optional[str]:
    """Extract version from filename or URL string (case-insensitive)."""

    temp = get_loader().extract_version_from_string(s)
    print(temp)
    return temp


def get_host_config(host_key: str) -> Optional[Dict[str, str]]:
    """Get host genome configuration."""
    return get_loader().get_host_config(host_key)

def get_software_url(name: str, repo_type: str = 'archives') -> Optional[str]:
    """Get software download URL."""
    return get_loader().get_software_url(name, repo_type)

def get_software_entry(name: str) -> Optional[Dict]:
    """Get software entry from sources.yaml (checks archives and git_repos).
    
    Args:
        name: Software name to look up
        
    Returns:
        Dict with url, description, file, branch or None if not found
    """
    software = get_loader().sources.get('software', {})
    
    archives = software.get('archives', {})
    if name in archives:
        return archives[name]
    
    git_repos = software.get('git_repos', {})
    if name in git_repos:
        return git_repos[name]
    
    return None

def get_git_url(name: str) -> Optional[str]:
    """Get Git repository URL."""
    return get_loader().get_git_url(name)

def get_ncbi_eutils_url(endpoint: str) -> Optional[str]:
    """Get NCBI E-utilities endpoint URL."""
    return get_loader().get_ncbi_eutils_url(endpoint)

def list_databases(category: Optional[str] = None):
    """List available databases."""
    return get_loader().list_databases(category)

def list_hosts():
    """List all host genomes."""
    return get_loader().list_hosts()

def list_software():
    """List all software."""
    return get_loader().list_software()


class LazySource:
    """Lazy loader for individual source entries."""
    
    def __init__(self, loader: SourceLoader, *keys: str):
        self._loader = loader
        self._keys = keys
        self._value = None
    
    def __str__(self) -> str:
        if self._value is None:
            self._value = self._loader.get(*self._keys)
        return str(self._value) if self._value else ""
    
    def __repr__(self) -> str:
        return f"LazySource({', '.join(repr(k) for k in self._keys)})"
    
    def get(self) -> Any:
        """Get the actual value."""
        if self._value is None:
            self._value = self._loader.get(*self._keys)
        return self._value


if __name__ == '__main__':
    print("TELE-Vir Source Configuration")
    print("=" * 50)
    print(f"Version: {version()}")
    print(f"Last Updated: {last_updated()}")
    print()
    
    print("Available Categories:")
    print("-" * 30)
    for section in sources().keys():
        if section not in ('version', 'last_updated'):
            print(f"  - {section}")
    print()
    
    print("Example Queries:")
    print("-" * 30)
    print(f"  Kraken2 viral URL: {get_db_url('kraken2', 'viral')}")
    print(f"  Human host config: {get_host_config('homo_sapiens')}")
    print(f"  FastQC URL: {get_software_url('fastqc')}")
    print(f"  SILVA 16S URL: {get_db_url('ribosomal_rna', 'silva_16s')}")
