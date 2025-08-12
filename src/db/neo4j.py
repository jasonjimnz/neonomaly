from neo4j import GraphDatabase
from core.config import settings
from typing import Any, Dict, List, Optional

class Neo4jDatabase:
    def __init__(self):
        self._driver = None

    def connect(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
        return self._driver

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return the results as a list of dictionaries."""
        driver = self.connect()
        with driver.session() as session:
            result = session.run(query, params or {})
            return [dict(record) for record in result]

    def execute_write_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a write query (CREATE, MERGE, DELETE, etc.)."""
        driver = self.connect()
        with driver.session() as session:
            result = session.write_transaction(lambda tx: tx.run(query, params or {}).data())
            return result

    def execute_read_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a read-only query (MATCH, etc.)."""
        driver = self.connect()
        with driver.session() as session:
            result = session.read_transaction(lambda tx: tx.run(query, params or {}).data())
            return result

# Create a singleton instance
db = Neo4jDatabase()