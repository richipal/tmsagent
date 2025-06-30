"""
Vector Search Service for entity resolution using ChromaDB.
Handles fuzzy string matching for database entities.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import spacy
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EntityMatch:
    """Represents a matched entity with confidence score."""
    original_text: str
    resolved_text: str
    confidence: float
    entity_type: str
    metadata: Dict[str, Any]


class VectorSearchService:
    """
    Service for vector-based entity resolution using ChromaDB.
    Handles fuzzy matching of user inputs to exact database values.
    """
    
    def __init__(self, persist_directory: str = None):
        """Initialize the vector search service."""
        from app.config.vector_config import vector_config
        
        self.config = vector_config
        self.persist_directory = persist_directory or self.config.VECTOR_DB_PERSIST_DIR
        self.embedding_model_name = self.config.EMBEDDING_MODEL_NAME
        self.confidence_threshold = self.config.CONFIDENCE_THRESHOLD
        
        # Initialize components
        self._init_chromadb()
        self._init_embedding_model()
        self._init_nlp_model()
        
        # Entity collections
        self.collections = {
            "employees": None,
            "locations": None,
            "departments": None,
            "activities": None
        }
        
        self._create_collections()
    
    def _init_chromadb(self):
        """Initialize ChromaDB client."""
        try:
            # Ensure directory exists
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Create ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=self.config.CHROMADB_ANONYMIZED_TELEMETRY,
                    allow_reset=self.config.CHROMADB_ALLOW_RESET
                )
            )
            logger.info(f"ChromaDB client initialized at: {self.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _init_embedding_model(self):
        """Initialize sentence transformer model for embeddings."""
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Sentence transformer model loaded: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _init_nlp_model(self):
        """Initialize spaCy NLP model for entity extraction."""
        try:
            # Try to load configured spaCy model
            try:
                self.nlp = spacy.load(self.config.SPACY_MODEL)
                logger.info(f"Loaded spaCy model: {self.config.SPACY_MODEL}")
            except OSError:
                logger.warning(f"spaCy model '{self.config.SPACY_MODEL}' not found. Please install with: python -m spacy download {self.config.SPACY_MODEL}")
                logger.info("Using blank spaCy model as fallback - entity extraction will be limited")
                # Use blank model as fallback
                self.nlp = spacy.blank("en")
            
            logger.info("spaCy NLP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load spaCy model: {e}")
            raise
    
    def _create_collections(self):
        """Create or get ChromaDB collections for different entity types."""
        try:
            for entity_type in self.collections.keys():
                collection_name = f"entities_{entity_type}"
                self.collections[entity_type] = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": f"Vector embeddings for {entity_type} entities"}
                )
            logger.info(f"Created/loaded collections: {list(self.collections.keys())}")
        except Exception as e:
            logger.error(f"Failed to create collections: {e}")
            raise
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract potential entities from text using spaCy NLP.
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            List of extracted entities with types and positions
        """
        doc = self.nlp(text)
        entities = []
        
        # Extract named entities using spaCy
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 1.0  # spaCy doesn't provide confidence scores by default
            })
        
        # If spaCy didn't find entities, use additional extraction methods
        if not entities:
            logger.debug("No entities found by spaCy, trying additional extraction methods")
            
            import re
            
            # Extract potential names from common query patterns (fallback for when spaCy fails)
            query_patterns = [
                r'(?:where does|who is|find|locate)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:work|works|working)',
                r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',  # Any two capitalized words
            ]
            
            for pattern in query_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    name = match.group(1) if match.lastindex else match.group(0)
                    # Check if this match is not already in entities
                    if not any(e["text"].lower() == name.lower() for e in entities):
                        start_pos = match.start(1) if match.lastindex else match.start()
                        entities.append({
                            "text": name,
                            "label": "PERSON",
                            "start": start_pos,
                            "end": start_pos + len(name),
                            "confidence": 0.8
                        })
        
        # Also extract proper nouns using spaCy's POS tagging
        for token in doc:
            if (token.pos_ == "PROPN" and token.is_alpha and len(token.text) > 2):
                # Check if this token is not already in entities
                if not any(e["start"] <= token.idx < e["end"] for e in entities):
                    # Look for sequences of proper nouns (likely names)
                    if token.i + 1 < len(doc) and doc[token.i + 1].pos_ == "PROPN":
                        # Two consecutive proper nouns - likely a person name
                        full_name = f"{token.text} {doc[token.i + 1].text}"
                        entities.append({
                            "text": full_name,
                            "label": "PERSON",
                            "start": token.idx,
                            "end": doc[token.i + 1].idx + len(doc[token.i + 1].text),
                            "confidence": 0.9
                        })
                    else:
                        # Single proper noun
                        entities.append({
                            "text": token.text,
                            "label": "PERSON_CANDIDATE",
                            "start": token.idx,
                            "end": token.idx + len(token.text),
                            "confidence": 0.7
                        })
        
        # Remove duplicates while preserving highest confidence
        unique_entities = {}
        for entity in entities:
            key = entity["text"].lower()
            if key not in unique_entities or entity["confidence"] > unique_entities[key]["confidence"]:
                unique_entities[key] = entity
        
        return list(unique_entities.values())
    
    def add_entity(self, entity_text: str, entity_type: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Add an entity to the vector database.
        
        Args:
            entity_text: The entity text to index
            entity_type: Type of entity (employees, locations, etc.)
            metadata: Additional metadata about the entity
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            if entity_type not in self.collections:
                logger.error(f"Unknown entity type: {entity_type}")
                return False
            
            collection = self.collections[entity_type]
            if collection is None:
                logger.error(f"Collection for {entity_type} not initialized")
                return False
            
            # Generate embedding
            embedding = self.embedding_model.encode([entity_text])[0].tolist()
            
            # Create unique ID
            entity_id = f"{entity_type}_{len(entity_text)}_{hash(entity_text) % 10000}"
            
            # Add to collection
            collection.add(
                embeddings=[embedding],
                documents=[entity_text],
                metadatas=[metadata or {}],
                ids=[entity_id]
            )
            
            logger.debug(f"Added entity '{entity_text}' to {entity_type} collection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add entity '{entity_text}': {e}")
            return False
    
    def search_similar_entities(self, query_text: str, entity_type: str, top_k: int = 5) -> List[EntityMatch]:
        """
        Search for similar entities in the vector database.
        
        Args:
            query_text: Text to search for
            entity_type: Type of entities to search in
            top_k: Number of top results to return
            
        Returns:
            List of EntityMatch objects with similarity scores
        """
        try:
            if entity_type not in self.collections:
                logger.error(f"Unknown entity type: {entity_type}")
                return []
            
            collection = self.collections[entity_type]
            if collection is None:
                logger.error(f"Collection for {entity_type} not initialized")
                return []
            
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([query_text])[0].tolist()
            
            # Search in collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert results to EntityMatch objects
            matches = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    # Convert distance to confidence score (ChromaDB uses cosine distance)
                    confidence = 1.0 - distance
                    
                    if confidence >= self.confidence_threshold:
                        matches.append(EntityMatch(
                            original_text=query_text,
                            resolved_text=doc,
                            confidence=confidence,
                            entity_type=entity_type,
                            metadata=metadata
                        ))
            
            logger.debug(f"Found {len(matches)} matches for '{query_text}' in {entity_type}")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to search for '{query_text}' in {entity_type}: {e}")
            return []
    
    def resolve_entity(self, entity_text: str, possible_types: List[str] = None) -> Optional[EntityMatch]:
        """
        Resolve a single entity to its exact database value.
        
        Args:
            entity_text: The entity text to resolve
            possible_types: List of entity types to search in (if None, searches all)
            
        Returns:
            Best EntityMatch if found, None otherwise
        """
        if possible_types is None:
            possible_types = list(self.collections.keys())
        
        best_match = None
        best_confidence = 0.0
        
        for entity_type in possible_types:
            matches = self.search_similar_entities(entity_text, entity_type, top_k=1)
            
            if matches and matches[0].confidence > best_confidence:
                best_match = matches[0]
                best_confidence = matches[0].confidence
        
        return best_match
    
    def resolve_query_entities(self, query: str) -> Tuple[str, List[EntityMatch]]:
        """
        Resolve all entities in a query and return the enhanced query.
        
        Args:
            query: Original user query
            
        Returns:
            Tuple of (enhanced_query, list_of_resolved_entities)
        """
        # Extract entities from query
        entities = self.extract_entities(query)
        resolved_entities = []
        enhanced_query = query
        
        # Sort entities by position (reverse order to maintain string indices)
        entities.sort(key=lambda x: x["start"], reverse=True)
        
        for entity in entities:
            entity_text = entity["text"]
            
            # Determine possible entity types based on spaCy label
            possible_types = self._get_possible_types(entity["label"])
            
            # Resolve entity
            resolved = self.resolve_entity(entity_text, possible_types)
            
            if resolved:
                # Replace in query
                start, end = entity["start"], entity["end"]
                enhanced_query = (enhanced_query[:start] + 
                                resolved.resolved_text + 
                                enhanced_query[end:])
                
                resolved_entities.append(resolved)
                logger.info(f"Resolved '{entity_text}' → '{resolved.resolved_text}' (confidence: {resolved.confidence:.3f})")
        
        return enhanced_query, resolved_entities
    
    def _get_possible_types(self, spacy_label: str) -> List[str]:
        """
        Map spaCy entity labels to our entity types.
        
        Args:
            spacy_label: spaCy entity label
            
        Returns:
            List of possible entity types to search
        """
        label_mapping = {
            "PERSON": ["employees"],
            "ORG": ["departments", "locations"],
            "GPE": ["locations"],  # Geopolitical entity
            "LOC": ["locations"],
            "PERSON_CANDIDATE": ["employees"]
        }
        
        return label_mapping.get(spacy_label, list(self.collections.keys()))
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database collections."""
        stats = {}
        
        for entity_type, collection in self.collections.items():
            if collection:
                try:
                    count = collection.count()
                    stats[entity_type] = {
                        "count": count,
                        "status": "active"
                    }
                except Exception as e:
                    stats[entity_type] = {
                        "count": 0,
                        "status": f"error: {e}"
                    }
            else:
                stats[entity_type] = {
                    "count": 0,
                    "status": "not_initialized"
                }
        
        return stats
    
    def reset_collection(self, entity_type: str) -> bool:
        """Reset a specific collection (clear all data)."""
        try:
            if entity_type not in self.collections:
                return False
            
            # Delete and recreate collection
            collection_name = f"entities_{entity_type}"
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass  # Collection might not exist
            
            self.collections[entity_type] = self.client.create_collection(
                name=collection_name,
                metadata={"description": f"Vector embeddings for {entity_type} entities"}
            )
            
            logger.info(f"Reset collection for {entity_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection {entity_type}: {e}")
            return False


# Global vector search service instance
vector_search_service = VectorSearchService()