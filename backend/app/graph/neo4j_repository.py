import logging
import os
import re
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


class GraphRepository:
    """
    Abstraction layer for graph operations.
    Uses Neo4j when available, falls back to an in-memory networkx graph.
    """
    def __init__(self):
        self._graph = nx.MultiDiGraph()
        self.driver = None
        self._use_neo4j = False

        uri = os.getenv("NEO4J_URI", "bolt://localhost:7688")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            from neo4j import AsyncGraphDatabase
            self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
            self._use_neo4j = True
            logger.info("Neo4j driver initialized at %s", uri)
        except Exception as e:
            logger.warning("Neo4j unavailable (%s), using in-memory graph.", e)

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def create_node(self, label: str, properties: dict[str, Any]):
        node_id = properties.get("id", str(id(properties)))

        if self._use_neo4j and self.driver:
            try:
                query = f"CREATE (n:{label} $props) RETURN n"
                async with self.driver.session() as session:
                    result = await session.run(query, props=properties)
                    record = await result.single()
                    # Mirror to in-memory graph
                    self._graph.add_node(node_id, label=label, **properties)
                    return record["n"].element_id if record else None
            except Exception as e:
                logger.warning("Neo4j create_node failed (%s), using in-memory graph.", e)
                self._use_neo4j = False

        # In-memory fallback
        self._graph.add_node(node_id, label=label, **properties)
        return node_id

    async def create_relationship(self, from_id: str, to_id: str, rel_type: str, properties: dict[str, Any] = None):
        if self._use_neo4j and self.driver:
            try:
                query = f"""
                MATCH (a), (b)
                WHERE a.id = $from_id AND b.id = $to_id
                CREATE (a)-[r:{rel_type} $props]->(b)
                RETURN r
                """
                async with self.driver.session() as session:
                    result = await session.run(query, from_id=from_id, to_id=to_id, props=properties or {})
                    record = await result.single()
                    # Mirror to in-memory graph
                    self._graph.add_edge(from_id, to_id, type=rel_type, **(properties or {}))
                    return record is not None
            except Exception as e:
                logger.warning("Neo4j create_relationship failed (%s), using in-memory graph.", e)
                self._use_neo4j = False

        # In-memory fallback
        self._graph.add_edge(from_id, to_id, type=rel_type, **(properties or {}))
        return True

    async def run_query(self, query: str, parameters: dict[str, Any] = None) -> list[dict[str, Any]]:
        if self._use_neo4j and self.driver:
            try:
                async with self.driver.session() as session:
                    result = await session.run(query, parameters or {})
                    records = await result.data()
                    return records
            except Exception as e:
                logger.warning("Neo4j run_query failed (%s), using in-memory graph.", e)
                self._use_neo4j = False

        # In-memory fallback: best-effort interpretation of a simple MATCH/WHERE/LIMIT
        # query — filters by any bound parameter value matching a node property
        # value, and respects a LIMIT clause, rather than unconditionally
        # dumping every node regardless of the query.
        nodes = [dict(self._graph.nodes[n]) for n in self._graph.nodes]

        if parameters:
            def matches(node: dict[str, Any]) -> bool:
                for value in parameters.values():
                    candidates = value if isinstance(value, (list, tuple, set)) else [value]
                    if any(candidate in node.values() for candidate in candidates):
                        return True
                return False

            nodes = [n for n in nodes if matches(n)]

        limit_match = re.search(r"LIMIT\s+(\d+)", query, re.IGNORECASE)
        if limit_match:
            nodes = nodes[: int(limit_match.group(1))]

        return [{"n": n} for n in nodes]


graph_repo = GraphRepository()
