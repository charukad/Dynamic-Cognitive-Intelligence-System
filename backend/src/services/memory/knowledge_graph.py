"""Knowledge graph service for managing graph memory."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from src.core import get_logger
from src.infrastructure.database import neo4j_client

logger = get_logger(__name__)


class KnowledgeGraphService:
    """
    Service for managing knowledge graph in Neo4j.
    
    Provides high-level operations for building and querying the knowledge graph.
    """

    def __init__(self) -> None:
        """Initialize knowledge graph service."""
        self.neo4j_client = neo4j_client
        self.client = self.neo4j_client

    async def add_concept(
        self,
        concept: str,
        concept_type: str = "Concept",
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a concept node to the knowledge graph.
        
        Args:
            concept: Concept name
            concept_type: Type of concept
            properties: Additional properties
            
        Returns:
            Created node
        """
        props = properties or {}
        props["name"] = concept
        props["type"] = concept_type
        
        node = await self.neo4j_client.create_node(
            label=concept_type,
            properties=props,
        )
        
        logger.info(f"Added concept: {concept} ({concept_type})")
        return node

    async def add_relationship(
        self,
        from_concept_id: str,
        to_concept_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a relationship between concepts.
        
        Args:
            from_concept_id: Source concept node ID
            to_concept_id: Target concept node ID
            relationship_type: Type of relationship (e.g., IS_A, RELATES_TO)
            properties: Additional properties
            
        Returns:
            Created relationship
        """
        rel = await self.neo4j_client.create_relationship(
            from_node_id=from_concept_id,
            to_node_id=to_concept_id,
            relationship_type=relationship_type,
            properties=properties,
        )
        
        logger.info(f"Added relationship: {from_concept_id} -{relationship_type}-> {to_concept_id}")
        return rel

    async def find_concepts(
        self,
        concept_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Find concepts by type and filters.
        
        Args:
            concept_type: Type of concept
            filters: Optional property filters
            limit: Maximum results
            
        Returns:
            Matching concepts
        """
        nodes = await self.neo4j_client.find_nodes(
            label=concept_type,
            properties=filters,
            limit=limit,
        )
        
        return nodes

    async def get_related_concepts(
        self,
        concept_id: str,
        relationship_type: Optional[str] = None,
        direction: str = "both",
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Get concepts related to a given concept.
        
        Args:
            concept_id: Source concept ID
            relationship_type: Optional relationship filter
            direction: Relationship direction
            limit: Maximum results
            
        Returns:
            Related concepts with relationships
        """
        neighbors = await self.neo4j_client.get_neighbors(
            node_id=concept_id,
            relationship_type=relationship_type,
            direction=direction,
            limit=limit,
        )
        
        return neighbors

    async def store_agent_knowledge(
        self,
        agent_id: UUID,
        knowledge: str,
        knowledge_type: str = "Knowledge",
    ) -> Dict[str, Any]:
        """
        Store knowledge learned by an agent.
        
        Args:
            agent_id: Agent UUID
            knowledge: Knowledge content
            knowledge_type: Type of knowledge
            
        Returns:
            Created knowledge node
        """
        # Create knowledge node
        knowledge_node = await self.add_concept(
            concept=knowledge,
            concept_type=knowledge_type,
            properties={
                "agent_id": str(agent_id),
                "content": knowledge,
            },
        )
        
        # Find or create agent node
        agent_nodes = await self.find_concepts(
            "Agent",
            filters={"agent_id": str(agent_id)},
        )
        
        if not agent_nodes:
            agent_node = await self.add_concept(
                concept=f"Agent_{agent_id}",
                concept_type="Agent",
                properties={"agent_id": str(agent_id)},
            )
        else:
            agent_node = agent_nodes[0]
        
        # Create LEARNED relationship
        if agent_node.get("id"):
            await self.add_relationship(
                from_concept_id=agent_node["id"],
                to_concept_id=knowledge_node.get("id", ""),
                relationship_type="LEARNED",
            )
        
        return knowledge_node

    async def store_task_outcome(
        self,
        task_id: UUID,
        outcome: str,
        success: bool,
    ) -> Dict[str, Any]:
        """
        Store task execution outcome in the graph.
        
        Args:
            task_id: Task UUID
            outcome: Outcome description
            success: Whether task succeeded
            
        Returns:
            Created outcome node
        """
        outcome_node = await self.add_concept(
            concept=f"Task_{task_id}_Outcome",
            concept_type="TaskOutcome",
            properties={
                "task_id": str(task_id),
                "outcome": outcome,
                "success": success,
            },
        )
        
        return outcome_node

    async def query_graph(
        self,
        cypher_query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.
        
        Args:
            cypher_query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Query results
        """
        results = await self.neo4j_client.execute_query(cypher_query, parameters)
        return results

    async def create_concept(
        self,
        concept: Optional[str] = None,
        concept_type: str = "Concept",
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Backward-compatible alias for add_concept used by legacy integration tests.
        """
        concept_name = concept or name
        if not concept_name:
            raise ValueError("Concept name is required")
        return await self.add_concept(concept=concept_name, concept_type=concept_type)

    async def create_relationship(
        self,
        from_concept: str,
        to_concept: str,
        relationship_type: str,
    ) -> Dict[str, Any]:
        """
        Backward-compatible relationship helper that accepts concept names.

        This delegates directly to the graph client; production flows should
        prefer ID-based add_relationship.
        """
        return await self.neo4j_client.create_relationship(
            from_node_id=from_concept,
            to_node_id=to_concept,
            relationship_type=relationship_type,
            properties=None,
        )

    async def find_related_concepts(self, concept_name: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Backward-compatible alias used by older tests.
        """
        query = (
            "MATCH (n {name: $name})-[*1..$max_depth]-(m) "
            "RETURN m LIMIT 25"
        )
        return await self.neo4j_client.execute_query(
            query,
            {"name": concept_name, "max_depth": max_depth},
        )


# Singleton instance
knowledge_graph_service = KnowledgeGraphService()
