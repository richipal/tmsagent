"""
Configuration for vector database and entity resolution settings.
"""

import os
from typing import Dict, Any


class VectorConfig:
    """Configuration class for vector database settings."""
    
    def __init__(self):
        """Initialize vector database configuration."""
        # Vector database settings
        self.VECTOR_DB_PERSIST_DIR = os.getenv("VECTOR_DB_PERSIST_DIR", "data/vector_db")
        self.EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        self.CONFIDENCE_THRESHOLD = float(os.getenv("VECTOR_CONFIDENCE_THRESHOLD", "0.5"))  # Lower threshold for better fuzzy matching
        self.MIN_QUERY_CONFIDENCE = float(os.getenv("MIN_QUERY_CONFIDENCE", "0.3"))      # Lower threshold for query enhancement
        
        # spaCy model settings
        self.SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
        
        # Entity indexing settings
        self.AUTO_INDEX_ON_STARTUP = os.getenv("AUTO_INDEX_ON_STARTUP", "false").lower() == "true"
        self.INDEX_REFRESH_INTERVAL_HOURS = int(os.getenv("INDEX_REFRESH_INTERVAL_HOURS", "24"))
        
        # ChromaDB settings
        self.CHROMADB_ANONYMIZED_TELEMETRY = False  # Disable to avoid telemetry errors
        self.CHROMADB_ALLOW_RESET = os.getenv("CHROMADB_ALLOW_RESET", "true").lower() == "true"
        
        # Entity resolution settings
        self.ENABLE_ENTITY_RESOLUTION = os.getenv("ENABLE_ENTITY_RESOLUTION", "true").lower() == "true"
        self.MAX_SUGGESTIONS_PER_ENTITY = int(os.getenv("MAX_SUGGESTIONS_PER_ENTITY", "3"))
        self.ENABLE_NO_RESULTS_SUGGESTIONS = os.getenv("ENABLE_NO_RESULTS_SUGGESTIONS", "true").lower() == "true"
        
        # Logging settings
        self.LOG_ENTITY_RESOLUTIONS = os.getenv("LOG_ENTITY_RESOLUTIONS", "true").lower() == "true"
        self.LOG_VECTOR_SEARCH_DETAILS = os.getenv("LOG_VECTOR_SEARCH_DETAILS", "false").lower() == "true"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "vector_db_persist_dir": self.VECTOR_DB_PERSIST_DIR,
            "embedding_model_name": self.EMBEDDING_MODEL_NAME,
            "confidence_threshold": self.CONFIDENCE_THRESHOLD,
            "min_query_confidence": self.MIN_QUERY_CONFIDENCE,
            "spacy_model": self.SPACY_MODEL,
            "auto_index_on_startup": self.AUTO_INDEX_ON_STARTUP,
            "index_refresh_interval_hours": self.INDEX_REFRESH_INTERVAL_HOURS,
            "chromadb_anonymized_telemetry": self.CHROMADB_ANONYMIZED_TELEMETRY,
            "chromadb_allow_reset": self.CHROMADB_ALLOW_RESET,
            "enable_entity_resolution": self.ENABLE_ENTITY_RESOLUTION,
            "max_suggestions_per_entity": self.MAX_SUGGESTIONS_PER_ENTITY,
            "enable_no_results_suggestions": self.ENABLE_NO_RESULTS_SUGGESTIONS,
            "log_entity_resolutions": self.LOG_ENTITY_RESOLUTIONS,
            "log_vector_search_details": self.LOG_VECTOR_SEARCH_DETAILS
        }
    
    def validate(self) -> Dict[str, Any]:
        """Validate configuration settings."""
        errors = []
        warnings = []
        
        # Validate confidence thresholds
        if not 0.0 <= self.CONFIDENCE_THRESHOLD <= 1.0:
            errors.append("CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
        
        if not 0.0 <= self.MIN_QUERY_CONFIDENCE <= 1.0:
            errors.append("MIN_QUERY_CONFIDENCE must be between 0.0 and 1.0")
        
        # Validate refresh interval
        if self.INDEX_REFRESH_INTERVAL_HOURS < 1:
            warnings.append("INDEX_REFRESH_INTERVAL_HOURS is less than 1 hour")
        
        # Validate max suggestions
        if self.MAX_SUGGESTIONS_PER_ENTITY < 1:
            errors.append("MAX_SUGGESTIONS_PER_ENTITY must be at least 1")
        elif self.MAX_SUGGESTIONS_PER_ENTITY > 10:
            warnings.append("MAX_SUGGESTIONS_PER_ENTITY is greater than 10, may affect performance")
        
        # Check if persist directory is writable (if it exists)
        if os.path.exists(self.VECTOR_DB_PERSIST_DIR):
            if not os.access(self.VECTOR_DB_PERSIST_DIR, os.W_OK):
                errors.append(f"Vector DB persist directory is not writable: {self.VECTOR_DB_PERSIST_DIR}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# Global configuration instance
vector_config = VectorConfig()


def get_vector_config() -> VectorConfig:
    """Get the global vector configuration instance."""
    return vector_config


def update_vector_config(**kwargs) -> None:
    """Update vector configuration with new values."""
    global vector_config
    
    for key, value in kwargs.items():
        if hasattr(vector_config, key.upper()):
            setattr(vector_config, key.upper(), value)


# Environment variable documentation
ENV_VAR_DOCS = {
    "VECTOR_DB_PERSIST_DIR": "Directory for persisting ChromaDB data (default: data/vector_db)",
    "EMBEDDING_MODEL_NAME": "SentenceTransformer model name (default: all-MiniLM-L6-v2)",
    "VECTOR_CONFIDENCE_THRESHOLD": "Minimum confidence for vector matches (default: 0.75)",
    "MIN_QUERY_CONFIDENCE": "Minimum confidence to use enhanced query (default: 0.6)",
    "SPACY_MODEL": "spaCy model for NLP processing (default: en_core_web_sm)",
    "AUTO_INDEX_ON_STARTUP": "Whether to build indexes on startup (default: false)",
    "INDEX_REFRESH_INTERVAL_HOURS": "Hours between automatic index refreshes (default: 24)",
    "CHROMADB_ANONYMIZED_TELEMETRY": "Enable ChromaDB telemetry (default: false)",
    "CHROMADB_ALLOW_RESET": "Allow resetting ChromaDB collections (default: true)",
    "ENABLE_ENTITY_RESOLUTION": "Enable entity resolution in queries (default: true)",
    "MAX_SUGGESTIONS_PER_ENTITY": "Maximum suggestions per entity (default: 3)",
    "ENABLE_NO_RESULTS_SUGGESTIONS": "Suggest corrections for no results (default: true)",
    "LOG_ENTITY_RESOLUTIONS": "Log entity resolution details (default: true)",
    "LOG_VECTOR_SEARCH_DETAILS": "Log detailed vector search info (default: false)"
}


def print_config_help() -> None:
    """Print help for vector database configuration environment variables."""
    print("Vector Database Configuration Environment Variables:")
    print("=" * 60)
    for var, description in ENV_VAR_DOCS.items():
        print(f"{var:<35} - {description}")
    print("=" * 60)