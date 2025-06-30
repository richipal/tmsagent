"""
Entity Indexer for building and maintaining vector indexes from BigQuery data.
Extracts entities from database and populates the vector search service.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
from .vector_search_service import vector_search_service
from ..data_science.sub_agents.bigquery.tools import bq_manager

logger = logging.getLogger(__name__)


@dataclass
class EntityStats:
    """Statistics about entity indexing process."""
    entity_type: str
    total_extracted: int
    successfully_indexed: int
    duplicates_skipped: int
    errors: List[str]


class EntityIndexer:
    """
    Builds and maintains vector indexes from BigQuery data.
    Extracts entities and populates ChromaDB collections.
    """
    
    def __init__(self):
        """Initialize the entity indexer."""
        self.vector_service = vector_search_service
        self.bq_manager = bq_manager
        
        # Configuration for entity extraction queries
        self.entity_extraction_config = {
            "employees": {
                "query": """
                    SELECT DISTINCT 
                        CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')) as full_name,
                        first_name,
                        last_name,
                        id as employee_id,
                        location_id
                    FROM `{project_id}.{dataset_id}.employee`
                    WHERE first_name IS NOT NULL AND last_name IS NOT NULL
                    AND TRIM(first_name) != '' AND TRIM(last_name) != ''
                """,
                "name_column": "full_name",
                "metadata_columns": ["first_name", "last_name", "employee_id", "location_id"]
            },
            
            "locations": {
                "query": """
                    SELECT DISTINCT 
                        name,
                        id as location_id,
                        code
                    FROM `{project_id}.{dataset_id}.location`
                    WHERE name IS NOT NULL 
                    AND TRIM(name) != ''
                """,
                "name_column": "name",
                "metadata_columns": ["location_id", "code"]
            },
            
            "activities": {
                "query": """
                    SELECT DISTINCT 
                        description as name,
                        id as activity_id,
                        code,
                        type as activity_type,
                        active
                    FROM `{project_id}.{dataset_id}.activity`
                    WHERE description IS NOT NULL 
                    AND TRIM(description) != ''
                """,
                "name_column": "name",
                "metadata_columns": ["activity_id", "code", "activity_type", "active"]
            }
        }
    
    async def build_all_indexes(self, reset_existing: bool = False) -> Dict[str, EntityStats]:
        """
        Build vector indexes for all entity types.
        
        Args:
            reset_existing: Whether to reset existing collections before building
            
        Returns:
            Dictionary of entity stats by entity type
        """
        logger.info("Starting to build all vector indexes")
        results = {}
        
        for entity_type in self.entity_extraction_config.keys():
            try:
                if reset_existing:
                    logger.info(f"Resetting collection for {entity_type}")
                    self.vector_service.reset_collection(entity_type)
                
                stats = await self.build_entity_index(entity_type)
                results[entity_type] = stats
                
            except Exception as e:
                logger.error(f"Failed to build index for {entity_type}: {e}")
                results[entity_type] = EntityStats(
                    entity_type=entity_type,
                    total_extracted=0,
                    successfully_indexed=0,
                    duplicates_skipped=0,
                    errors=[str(e)]
                )
        
        # Log summary
        total_indexed = sum(stats.successfully_indexed for stats in results.values())
        total_errors = sum(len(stats.errors) for stats in results.values())
        
        logger.info(f"Index building complete. Total entities indexed: {total_indexed}, Total errors: {total_errors}")
        
        return results
    
    async def build_entity_index(self, entity_type: str) -> EntityStats:
        """
        Build vector index for a specific entity type.
        
        Args:
            entity_type: Type of entity to index (employees, locations, etc.)
            
        Returns:
            EntityStats with indexing results
        """
        if entity_type not in self.entity_extraction_config:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        config = self.entity_extraction_config[entity_type]
        stats = EntityStats(
            entity_type=entity_type,
            total_extracted=0,
            successfully_indexed=0,
            duplicates_skipped=0,
            errors=[]
        )
        
        try:
            # Extract entities from BigQuery
            entities = await self._extract_entities_from_bigquery(entity_type, config)
            stats.total_extracted = len(entities)
            
            logger.info(f"Extracted {len(entities)} {entity_type} from BigQuery")
            
            # Track duplicates
            seen_names = set()
            
            # Index each entity
            for entity in entities:
                try:
                    entity_name = entity.get(config["name_column"], "").strip()
                    if not entity_name:
                        continue
                    
                    # Check for duplicates (case-insensitive)
                    name_lower = entity_name.lower()
                    if name_lower in seen_names:
                        stats.duplicates_skipped += 1
                        continue
                    
                    seen_names.add(name_lower)
                    
                    # Create metadata
                    metadata = {
                        "entity_type": entity_type,
                        "source": "bigquery"
                    }
                    
                    # Add configured metadata columns
                    for col in config["metadata_columns"]:
                        if col in entity and entity[col] is not None:
                            metadata[col] = str(entity[col])
                    
                    # Add to vector database
                    success = self.vector_service.add_entity(
                        entity_text=entity_name,
                        entity_type=entity_type,
                        metadata=metadata
                    )
                    
                    if success:
                        stats.successfully_indexed += 1
                    else:
                        stats.errors.append(f"Failed to index entity: {entity_name}")
                
                except Exception as e:
                    error_msg = f"Error indexing entity {entity.get(config['name_column'], 'unknown')}: {e}"
                    stats.errors.append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"Successfully indexed {stats.successfully_indexed}/{stats.total_extracted} {entity_type}")
            
        except Exception as e:
            error_msg = f"Failed to build index for {entity_type}: {e}"
            stats.errors.append(error_msg)
            logger.error(error_msg)
        
        return stats
    
    async def _extract_entities_from_bigquery(self, entity_type: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract entities from BigQuery using the configured query.
        
        Args:
            entity_type: Type of entity to extract
            config: Configuration for the entity type
            
        Returns:
            List of entity records from BigQuery
        """
        # Format the query with project and dataset IDs
        query = config["query"].format(
            project_id=self.bq_manager.project_id,
            dataset_id=self.bq_manager.dataset_id
        )
        
        logger.debug(f"Executing BigQuery extraction for {entity_type}:\n{query}")
        
        # Execute the query
        result = self.bq_manager.execute_query(query)
        
        if "error" in result:
            raise Exception(f"BigQuery extraction failed: {result['error']}")
        
        return result.get("data", [])
    
    def get_indexing_stats(self) -> Dict[str, Any]:
        """
        Get current statistics about the vector database indexes.
        
        Returns:
            Dictionary with indexing statistics
        """
        stats = self.vector_service.get_collection_stats()
        
        # Add additional metadata
        enhanced_stats = {
            "collections": stats,
            "total_entities": sum(collection.get("count", 0) for collection in stats.values()),
            "available_entity_types": list(self.entity_extraction_config.keys()),
            "indexer_status": "ready"
        }
        
        return enhanced_stats
    
    async def refresh_entity_index(self, entity_type: str) -> EntityStats:
        """
        Refresh the index for a specific entity type.
        This will reset and rebuild the index with current BigQuery data.
        
        Args:
            entity_type: Type of entity to refresh
            
        Returns:
            EntityStats with refresh results
        """
        logger.info(f"Refreshing index for {entity_type}")
        
        # Reset the collection
        success = self.vector_service.reset_collection(entity_type)
        if not success:
            raise Exception(f"Failed to reset collection for {entity_type}")
        
        # Rebuild the index
        return await self.build_entity_index(entity_type)
    
    async def add_custom_entities(self, entity_type: str, entities: List[Dict[str, str]]) -> int:
        """
        Add custom entities to the vector database.
        
        Args:
            entity_type: Type of entity to add
            entities: List of entities, each with 'name' and optional metadata
            
        Returns:
            Number of entities successfully added
        """
        if entity_type not in self.vector_service.collections:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        success_count = 0
        
        for entity in entities:
            entity_name = entity.get("name", "").strip()
            if not entity_name:
                continue
            
            # Create metadata
            metadata = {
                "entity_type": entity_type,
                "source": "custom",
                **{k: v for k, v in entity.items() if k != "name"}
            }
            
            success = self.vector_service.add_entity(
                entity_text=entity_name,
                entity_type=entity_type,
                metadata=metadata
            )
            
            if success:
                success_count += 1
        
        logger.info(f"Added {success_count}/{len(entities)} custom {entity_type}")
        return success_count
    
    def validate_entity_extraction_config(self) -> Dict[str, Any]:
        """
        Validate that the entity extraction configuration is correct.
        
        Returns:
            Validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check that all configured entity types have valid collections
        for entity_type in self.entity_extraction_config.keys():
            if entity_type not in self.vector_service.collections:
                validation_results["errors"].append(f"No collection defined for entity type: {entity_type}")
                validation_results["valid"] = False
        
        # Check BigQuery connectivity
        try:
            datasets = self.bq_manager.get_datasets()
            if not datasets:
                validation_results["warnings"].append("No datasets found in BigQuery")
            elif self.bq_manager.dataset_id not in datasets:
                validation_results["errors"].append(f"Target dataset '{self.bq_manager.dataset_id}' not found")
                validation_results["valid"] = False
        except Exception as e:
            validation_results["errors"].append(f"BigQuery connectivity issue: {e}")
            validation_results["valid"] = False
        
        # Check required tables exist
        try:
            tables = self.bq_manager.get_tables()
            required_tables = {"employee", "location", "activity"}
            missing_tables = required_tables - set(tables)
            
            if missing_tables:
                validation_results["errors"].append(f"Missing required tables: {missing_tables}")
                validation_results["valid"] = False
        except Exception as e:
            validation_results["warnings"].append(f"Could not verify table existence: {e}")
        
        return validation_results


# Global entity indexer instance
entity_indexer = EntityIndexer()