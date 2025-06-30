#!/usr/bin/env python3
"""
Script to index entities from BigQuery into the vector database.
Can be run standalone or imported as a module.
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.entity_indexer import entity_indexer
from app.config.vector_config import vector_config, print_config_help


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def index_all_entities(reset_existing: bool = False, verbose: bool = False) -> None:
    """Index all entity types from BigQuery."""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting entity indexing process")
    logger.info(f"Vector DB directory: {vector_config.VECTOR_DB_PERSIST_DIR}")
    logger.info(f"Reset existing collections: {reset_existing}")
    
    try:
        # Validate configuration
        config_validation = vector_config.validate()
        if not config_validation["valid"]:
            logger.error("Configuration validation failed:")
            for error in config_validation["errors"]:
                logger.error(f"  - {error}")
            return
        
        if config_validation["warnings"]:
            logger.warning("Configuration warnings:")
            for warning in config_validation["warnings"]:
                logger.warning(f"  - {warning}")
        
        # Validate entity extraction configuration
        validation_result = entity_indexer.validate_entity_extraction_config()
        if not validation_result["valid"]:
            logger.error("Entity extraction configuration validation failed:")
            for error in validation_result["errors"]:
                logger.error(f"  - {error}")
            return
        
        if validation_result["warnings"]:
            logger.warning("Entity extraction warnings:")
            for warning in validation_result["warnings"]:
                logger.warning(f"  - {warning}")
        
        # Build all indexes
        results = await entity_indexer.build_all_indexes(reset_existing=reset_existing)
        
        # Print results summary
        print("\n" + "="*60)
        print("ENTITY INDEXING RESULTS")
        print("="*60)
        
        total_indexed = 0
        total_errors = 0
        
        for entity_type, stats in results.items():
            print(f"\n{entity_type.upper()}:")
            print(f"  Total extracted: {stats.total_extracted}")
            print(f"  Successfully indexed: {stats.successfully_indexed}")
            print(f"  Duplicates skipped: {stats.duplicates_skipped}")
            print(f"  Errors: {len(stats.errors)}")
            
            if stats.errors and verbose:
                print("  Error details:")
                for error in stats.errors[:5]:  # Show first 5 errors
                    print(f"    - {error}")
                if len(stats.errors) > 5:
                    print(f"    ... and {len(stats.errors) - 5} more errors")
            
            total_indexed += stats.successfully_indexed
            total_errors += len(stats.errors)
        
        print(f"\nTOTAL SUMMARY:")
        print(f"  Total entities indexed: {total_indexed}")
        print(f"  Total errors: {total_errors}")
        
        # Show final collection stats
        indexing_stats = entity_indexer.get_indexing_stats()
        print(f"\nFINAL COLLECTION STATS:")
        for entity_type, collection_stats in indexing_stats["collections"].items():
            status = collection_stats.get("status", "unknown")
            count = collection_stats.get("count", 0)
            print(f"  {entity_type}: {count} entities ({status})")
        
        print("="*60)
        
        if total_errors == 0:
            logger.info("Entity indexing completed successfully!")
        else:
            logger.warning(f"Entity indexing completed with {total_errors} errors")
        
    except Exception as e:
        logger.error(f"Entity indexing failed: {e}")
        if verbose:
            logger.exception("Full error details:")


async def index_specific_entity(entity_type: str, refresh: bool = False, verbose: bool = False) -> None:
    """Index a specific entity type."""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Indexing {entity_type}")
    
    try:
        if refresh:
            stats = await entity_indexer.refresh_entity_index(entity_type)
        else:
            stats = await entity_indexer.build_entity_index(entity_type)
        
        print(f"\n{entity_type.upper()} INDEXING RESULTS:")
        print(f"  Total extracted: {stats.total_extracted}")
        print(f"  Successfully indexed: {stats.successfully_indexed}")
        print(f"  Duplicates skipped: {stats.duplicates_skipped}")
        print(f"  Errors: {len(stats.errors)}")
        
        if stats.errors and verbose:
            print("  Error details:")
            for error in stats.errors:
                print(f"    - {error}")
        
        logger.info(f"Indexing {entity_type} completed")
        
    except Exception as e:
        logger.error(f"Failed to index {entity_type}: {e}")
        if verbose:
            logger.exception("Full error details:")


def show_current_stats() -> None:
    """Show current indexing statistics."""
    try:
        stats = entity_indexer.get_indexing_stats()
        
        print("\nCURRENT VECTOR DATABASE STATS:")
        print("="*40)
        print(f"Total entities: {stats['total_entities']}")
        print(f"Available entity types: {', '.join(stats['available_entity_types'])}")
        print(f"Indexer status: {stats['indexer_status']}")
        
        print(f"\nCOLLECTION DETAILS:")
        for entity_type, collection_stats in stats["collections"].items():
            status = collection_stats.get("status", "unknown")
            count = collection_stats.get("count", 0)
            print(f"  {entity_type}: {count} entities ({status})")
        
    except Exception as e:
        print(f"Error getting stats: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Index entities from BigQuery into vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python index_entities.py --all                    # Index all entity types
  python index_entities.py --all --reset            # Reset and rebuild all indexes
  python index_entities.py --entity employees       # Index only employees
  python index_entities.py --entity locations --refresh  # Refresh locations index
  python index_entities.py --stats                  # Show current statistics
  python index_entities.py --config-help            # Show configuration help
        """
    )
    
    parser.add_argument("--all", action="store_true", help="Index all entity types")
    parser.add_argument("--entity", help="Index specific entity type (employees, locations, departments, activities)")
    parser.add_argument("--reset", action="store_true", help="Reset existing collections before indexing (use with --all)")
    parser.add_argument("--refresh", action="store_true", help="Refresh specific entity index (use with --entity)")
    parser.add_argument("--stats", action="store_true", help="Show current indexing statistics")
    parser.add_argument("--config-help", action="store_true", help="Show configuration environment variables")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.config_help:
        print_config_help()
        return
    
    if args.stats:
        show_current_stats()
        return
    
    if args.all:
        asyncio.run(index_all_entities(reset_existing=args.reset, verbose=args.verbose))
    elif args.entity:
        valid_entities = ["employees", "locations", "activities"]
        if args.entity not in valid_entities:
            print(f"Error: Invalid entity type '{args.entity}'. Valid options: {', '.join(valid_entities)}")
            sys.exit(1)
        
        asyncio.run(index_specific_entity(args.entity, refresh=args.refresh, verbose=args.verbose))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()