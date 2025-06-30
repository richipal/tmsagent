"""
Entity Resolver for mapping fuzzy user inputs to exact database values.
Works with VectorSearchService to enhance SQL query generation.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from .vector_search_service import vector_search_service, EntityMatch

logger = logging.getLogger(__name__)


@dataclass
class ResolutionResult:
    """Result of entity resolution process."""
    original_query: str
    enhanced_query: str
    resolved_entities: List[EntityMatch]
    confidence_score: float
    fallback_to_original: bool


class EntityResolver:
    """
    Resolves fuzzy user inputs to exact database values using vector search.
    Enhances SQL query generation with entity resolution.
    """
    
    def __init__(self):
        """Initialize the entity resolver."""
        from app.config.vector_config import vector_config
        
        self.config = vector_config
        self.vector_service = vector_search_service
        self.min_query_confidence = self.config.MIN_QUERY_CONFIDENCE
        
        # Common patterns for entity detection
        self.name_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # First Last
            r'\b[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+\b',  # First M. Last
            r'\b[A-Z][a-z]+, [A-Z][a-z]+\b',  # Last, First
        ]
        
        self.location_indicators = [
            'school', 'university', 'college', 'hospital', 'clinic',
            'department', 'office', 'building', 'center', 'facility',
            'HS', 'MS', 'ES'  # High School, Middle School, Elementary School
        ]
    
    def enhance_query(self, user_query: str, context: Dict[str, Any] = None) -> ResolutionResult:
        """
        Enhance a user query by resolving fuzzy entities to exact database values.
        
        Args:
            user_query: Original user query
            context: Additional context for resolution
            
        Returns:
            ResolutionResult with enhanced query and resolution details
        """
        logger.info(f"Starting entity resolution for query: '{user_query}'")
        
        try:
            # Step 1: Extract and resolve entities
            enhanced_query, resolved_entities = self.vector_service.resolve_query_entities(user_query)
            
            # Debug: Log what entities were extracted
            extracted_entities = self.vector_service.extract_entities(user_query)
            if extracted_entities:
                logger.debug(f"Extracted {len(extracted_entities)} entities from query:")
                for entity in extracted_entities:
                    logger.debug(f"  - '{entity['text']}' (type: {entity['label']}, confidence: {entity.get('confidence', 'N/A')})")
            else:
                logger.debug("No entities extracted from query")
            
            # Step 2: Calculate overall confidence
            confidence_score = self._calculate_confidence(user_query, resolved_entities)
            
            # Step 3: Decide whether to use enhanced query or fall back
            fallback_to_original = confidence_score < self.min_query_confidence
            
            final_query = user_query if fallback_to_original else enhanced_query
            
            result = ResolutionResult(
                original_query=user_query,
                enhanced_query=final_query,
                resolved_entities=resolved_entities,
                confidence_score=confidence_score,
                fallback_to_original=fallback_to_original
            )
            
            # Log resolution results
            if resolved_entities:
                logger.info(f"Entity resolution results:")
                for entity in resolved_entities:
                    logger.info(f"  '{entity.original_text}' → '{entity.resolved_text}' "
                              f"({entity.entity_type}, confidence: {entity.confidence:.3f})")
                logger.info(f"Overall confidence: {confidence_score:.3f}")
                logger.info(f"Final query: '{final_query}'")
            else:
                logger.info("No entities resolved")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in entity resolution: {e}")
            # Return original query on error
            return ResolutionResult(
                original_query=user_query,
                enhanced_query=user_query,
                resolved_entities=[],
                confidence_score=0.0,
                fallback_to_original=True
            )
    
    def _calculate_confidence(self, original_query: str, resolved_entities: List[EntityMatch]) -> float:
        """
        Calculate overall confidence score for the resolution.
        
        Args:
            original_query: Original user query
            resolved_entities: List of resolved entities
            
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not resolved_entities:
            return 1.0  # No changes needed, full confidence in original
        
        # Calculate weighted average of entity confidences
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for entity in resolved_entities:
            # Weight by entity text length (longer entities are more important)
            weight = len(entity.original_text)
            weighted_confidence += entity.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_confidence / total_weight
    
    def suggest_corrections(self, user_query: str, max_suggestions: int = None) -> List[Dict[str, Any]]:
        """
        Suggest possible corrections for entities in the query.
        
        Args:
            user_query: Original user query
            max_suggestions: Maximum number of suggestions per entity (uses config if None)
            
        Returns:
            List of correction suggestions
        """
        if max_suggestions is None:
            max_suggestions = self.config.MAX_SUGGESTIONS_PER_ENTITY
        
        suggestions = []
        entities = self.vector_service.extract_entities(user_query)
        
        for entity in entities:
            entity_text = entity["text"]
            possible_types = self.vector_service._get_possible_types(entity["label"])
            
            # Get multiple matches for suggestions
            for entity_type in possible_types:
                matches = self.vector_service.search_similar_entities(
                    entity_text, entity_type, top_k=max_suggestions
                )
                
                for match in matches:
                    if match.resolved_text.lower() != entity_text.lower():
                        suggestions.append({
                            "original": entity_text,
                            "suggestion": match.resolved_text,
                            "confidence": match.confidence,
                            "entity_type": entity_type,
                            "reason": f"Similar {entity_type.rstrip('s')} found"
                        })
        
        # Sort by confidence and limit results
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:max_suggestions * 2]  # Return top suggestions across all entities
    
    def validate_entity_existence(self, entity_text: str, entity_type: str) -> bool:
        """
        Check if an entity exists in the database.
        
        Args:
            entity_text: Entity text to validate
            entity_type: Type of entity to check
            
        Returns:
            True if entity exists (high confidence match), False otherwise
        """
        matches = self.vector_service.search_similar_entities(entity_text, entity_type, top_k=1)
        
        if matches and matches[0].confidence > 0.9:
            # Very high confidence match means entity likely exists
            return True
        
        return False
    
    def get_resolution_context_for_prompt(self, resolution_result: ResolutionResult) -> str:
        """
        Generate context text for inclusion in NL2SQL prompts.
        
        Args:
            resolution_result: Result from enhance_query()
            
        Returns:
            Context string for prompt enhancement
        """
        if not resolution_result.resolved_entities:
            return ""
        
        context_parts = ["ENTITY RESOLUTION CONTEXT:"]
        
        for entity in resolution_result.resolved_entities:
            context_parts.append(
                f"- User input '{entity.original_text}' resolved to '{entity.resolved_text}' "
                f"(type: {entity.entity_type}, confidence: {entity.confidence:.2f})"
            )
        
        if resolution_result.fallback_to_original:
            context_parts.append("Note: Low confidence resolution, using original query")
        else:
            context_parts.append(f"Overall confidence: {resolution_result.confidence_score:.2f}")
        
        context_parts.append("")  # Empty line for separation
        
        return "\n".join(context_parts)
    
    def preprocess_for_sql_generation(self, user_query: str, context: Dict[str, Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Preprocess user query for SQL generation with entity resolution.
        
        Args:
            user_query: Original user query
            context: Additional context
            
        Returns:
            Tuple of (processed_query, enhanced_context)
        """
        # Perform entity resolution
        resolution_result = self.enhance_query(user_query, context)
        
        # Create enhanced context
        enhanced_context = dict(context) if context else {}
        enhanced_context.update({
            "entity_resolution": {
                "performed": True,
                "original_query": resolution_result.original_query,
                "enhanced_query": resolution_result.enhanced_query,
                "resolved_entities": [
                    {
                        "original": e.original_text,
                        "resolved": e.resolved_text,
                        "type": e.entity_type,
                        "confidence": e.confidence
                    } for e in resolution_result.resolved_entities
                ],
                "confidence_score": resolution_result.confidence_score,
                "fallback_used": resolution_result.fallback_to_original
            }
        })
        
        # Get context for prompt
        prompt_context = self.get_resolution_context_for_prompt(resolution_result)
        enhanced_context["resolution_context"] = prompt_context
        
        return resolution_result.enhanced_query, enhanced_context
    
    def handle_no_results_case(self, user_query: str, sql_query: str) -> Dict[str, Any]:
        """
        Handle the case when SQL returns no results - suggest corrections.
        
        Args:
            user_query: Original user query
            sql_query: Generated SQL that returned no results
            
        Returns:
            Dictionary with suggestions and analysis
        """
        logger.info(f"Handling no results case for query: '{user_query}'")
        
        # Get entity suggestions
        suggestions = self.suggest_corrections(user_query)
        
        # Analyze the query for common issues
        analysis = {
            "likely_issues": [],
            "suggestions": suggestions,
            "recommended_actions": []
        }
        
        # Check for potential spelling/abbreviation issues
        entities = self.vector_service.extract_entities(user_query)
        for entity in entities:
            entity_text = entity["text"]
            
            # Check if entity has potential matches
            possible_types = self.vector_service._get_possible_types(entity["label"])
            has_similar = False
            
            for entity_type in possible_types:
                matches = self.vector_service.search_similar_entities(entity_text, entity_type, top_k=1)
                if matches and matches[0].confidence > 0.5:
                    has_similar = True
                    break
            
            if has_similar:
                analysis["likely_issues"].append(f"'{entity_text}' might be misspelled or abbreviated")
        
        # Add recommendations
        if suggestions:
            analysis["recommended_actions"].append("Try the suggested corrections above")
        
        analysis["recommended_actions"].extend([
            "Check spelling of names and locations",
            "Try using different variations (e.g., 'HS' vs 'High School')",
            "Verify the entity exists in the database"
        ])
        
        return analysis


# Global entity resolver instance
entity_resolver = EntityResolver()