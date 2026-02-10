"""Neo4j graph database client."""

from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver

from src.core import get_logger, settings

logger = get_logger(__name__)


class Neo4jClient:
    """
    Neo4j client for knowledge graph operations.
    
    Manages connections and Cypher query execution.
    """

    def __init__(self):
        """Initialize Neo4j client."""
        self.driver: Optional[AsyncDriver] = None
        self.uri = settings.neo4j_uri
        self.user = settings.neo4j_user
        self.password = settings.neo4j_password

    async def connect(self) -> None:
        """Connect to Neo4j database."""
        if self.driver is not None:
            logger.warning("Neo4j driver already connected")
            return

        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )
            
            # Verify connectivity
            await self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            if self.driver:
                await self.driver.close()
                self.driver = None
            raise

    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self.driver is None:
            return

        try:
            await self.driver.close()
            self.driver = None
            logger.info("Neo4j driver closed")
            
        except Exception as e:
            logger.error(f"Error closing Neo4j driver: {e}")
    
    async def health_check(self) -> bool:
        """
        Verify Neo4j connection is healthy.
        
        Returns:
            True if healthy
            
        Raises:
            RuntimeError: If health check fails
        """
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized")
        
        try:
            # Verify connectivity
            await self.driver.verify_connectivity()
            
            # Test query execution
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as health")
                await result.single()
            
            logger.debug("Neo4j health check passed")
            return True
            
        except Exception as e:
            raise RuntimeError(f"Neo4j health check failed: {e}") from e


    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        if self.driver is None:
            await self.connect()

        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a node in the graph.
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            Created node
        """
        query = f"""
        CREATE (n:{label} $props)
        RETURN n
        """
        
        results = await self.execute_query(query, {"props": properties})
        return results[0]["n"] if results else {}

    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a relationship between two nodes.
        
        Args:
            from_id: Source node ID
            to_id: Target node ID
            rel_type: Relationship type
            properties: Relationship properties
            
        Returns:
            Created relationship
        """
        query = f"""
        MATCH (a {{id: $from_id}})
        MATCH (b {{id: $to_id}})
        CREATE (a)-[r:{rel_type} $props]->(b)
        RETURN r
        """
        
        results = await self.execute_query(
            query,
            {"from_id": from_id, "to_id": to_id, "props": properties or {}},
        )
        return results[0]["r"] if results else {}

    async def find_nodes(
        self,
        label: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Find nodes matching criteria.
        
        Args:
            label: Node label
            filters: Property filters
            limit: Maximum results
            
        Returns:
            List of matching nodes
        """
        where_clause = ""
        if filters:
            conditions = [f"n.{k} = ${k}" for k in filters.keys()]
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
        MATCH (n:{label})
        {where_clause}
        RETURN n
        LIMIT {limit}
        """
        
        results = await self.execute_query(query, filters or {})
        return [r["n"] for r in results]

    async def find_path(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Find shortest path between two nodes.
        
        Args:
            from_id: Source node ID
            to_id: Target node ID
            max_depth: Maximum path length
            
        Returns:
            Path information
        """
        query = f"""
        MATCH path = shortestPath(
            (a {{id: $from_id}})-[*1..{max_depth}]-(b {{id: $to_id}})
        )
        RETURN path
        """
        
        return await self.execute_query(query, {"from_id": from_id, "to_id": to_id})

    async def init_schema(self) -> None:
        """Initialize graph schema constraints and indexes."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Concept) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Agent) REQUIRE n.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Task) REQUIRE n.id IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (n:Concept) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Agent) ON (n.type)",
        ]

        for constraint in constraints:
            await self.execute_query(constraint)

        logger.info("Neo4j schema initialized")


# Global instance
neo4j_client = Neo4jClient()
