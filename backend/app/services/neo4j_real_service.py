from neo4j import GraphDatabase
from typing import List, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jRealService:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            # Potentially raise an exception or handle reconnection strategy
            raise

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed.")

    def _execute_query(self, query: str, parameters: dict = None) -> List[Dict[str, Any]]:
        with self.driver.session(database=settings.NEO4J_DATABASE) as session:
            try:
                result = session.run(query, parameters)
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Neo4j query failed: {query} | Parameters: {parameters} | Error: {e}")
                # Depending on the error, you might want to raise it or return an empty list/specific error indicator
                raise # Or return [] or a custom error object

    def create_bridge_entity(self, entity_type: str, properties: dict) -> str:
        # Ensure properties are suitable for Cypher query
        # Basic sanitization: escape quotes in string properties if any (though parameters usually handle this)
        # For simplicity, assuming properties are well-formed for now.

        # Create a unique ID for the node if not provided. Using Neo4j's internal ID is also an option.
        # For now, let's assume a 'name' property can act as a unique identifier for simplicity in this example.
        # A more robust approach would be to use a UUID or ensure 'name' is indeed unique.

        # Constructing the SET part of the query dynamically
        set_clauses = ", ".join([f"n.{key} = ${key}" for key in properties.keys()])

        # Add a 'name' property if it's not in properties, as it's often used for identification.
        # This is a placeholder; a proper ID management strategy is needed.
        if 'name' not in properties and 'id' not in properties:
            # If no 'name' or 'id', we can't reliably return an identifier without creating one.
            # Let's assume for now that the calling code ensures a unique 'name' or similar property.
            # Or, we can use Neo4j's internal ID.
            pass

        query = f"""
        CREATE (n:{entity_type} {{{set_clauses}}})
        RETURN elementId(n) AS id, n AS node_properties
        """
        # Parameters are properties plus any other needed for the query
        # query_params = {**properties} # Not needed if properties are directly used with $key syntax

        try:
            result = self._execute_query(query, properties)
            if result:
                # Return Neo4j's internal element ID
                return result[0].get('id')
            return None
        except Exception as e:
            logger.error(f"Error creating bridge entity ({entity_type} with props {properties}): {e}")
            return None


    def create_relationship_by_element_ids(self, start_node_element_id: str, end_node_element_id: str, rel_type: str, properties: dict = None) -> bool:
        """
        Creates a relationship between two nodes identified by their Neo4j element IDs.
        """
        properties = properties or {}
        # Constructing the SET part of the query dynamically for relationship properties
        set_clauses = ""
        if properties:
            set_clauses = "SET " + ", ".join([f"r.{key} = ${key}" for key in properties.keys()])

        query = f"""
        MATCH (a), (b)
        WHERE elementId(a) = $start_node_element_id AND elementId(b) = $end_node_element_id
        CREATE (a)-[r:{rel_type} {{{', '.join([f"{key}: ${key}" for key in properties.keys()])}}}]->(b)
        RETURN elementId(r) AS relId
        """

        # Parameters for the query include the element IDs and any relationship properties
        params = {
            "start_node_element_id": start_node_element_id,
            "end_node_element_id": end_node_element_id,
            **properties  # Spread relationship properties into the params dict
        }

        try:
            result = self._execute_query(query, params)
            return len(result) > 0 and result[0].get('relId') is not None
        except Exception as e:
            logger.error(f"Error creating relationship by element IDs ({start_node_element_id}-[{rel_type}]->{end_node_element_id}): {e}")
            return False

    def search_entities(self, keywords: List[str], entity_types: List[str] = None) -> List[Dict]:
        # Basic keyword search: checks if node properties contain any of the keywords.
        # This is a simple full-text search; for more advanced search, consider Neo4j's full-text indexing.

        # Constructing the WHERE clause for entity types
        type_filter_clause = ""
        if entity_types:
            type_conditions = " OR ".join([f"label = '{etype}'" for etype in entity_types])
            type_filter_clause = f"AND ({type_conditions})" # This is incorrect for labels, labels are not properties

        # Corrected type filter:
        if entity_types:
            type_filter_clause = " AND (" + " OR ".join([f"n:{etype}" for etype in entity_types]) + ")"

        # Constructing the WHERE clause for keywords (searching in 'name' property for this example)
        # A more comprehensive search would iterate over all string properties or use full-text search.
        keyword_conditions = []
        params = {}
        for i, keyword in enumerate(keywords):
            param_name = f"keyword{i}"
            keyword_conditions.append(f"n.name CONTAINS ${param_name}") # Assuming search in 'name'
            params[param_name] = keyword

        if not keyword_conditions: # If no keywords, maybe return all entities of given types or nothing
            if not entity_types: return [] # Or handle as an error / return all nodes
            keyword_filter_clause = ""
        else:
            keyword_filter_clause = "WHERE " + " OR ".join(keyword_conditions)


        # If only type filter is present and no keywords
        if not keyword_filter_clause and type_filter_clause:
             query = f"""
             MATCH (n)
             WHERE {" AND ".join(type_filter_clause.strip(" AND ()").split(" OR "))}
             RETURN n, labels(n) as types
             """
        # If only keyword filter is present and no types
        elif keyword_filter_clause and not type_filter_clause:
            query = f"""
            MATCH (n)
            {keyword_filter_clause}
            RETURN n, labels(n) as types
            """
        # If both are present
        elif keyword_filter_clause and type_filter_clause:
            query = f"""
            MATCH (n)
            {keyword_filter_clause} {type_filter_clause}
            RETURN n, labels(n) as types
            """
        # If neither is present (e.g. get all nodes, or handle as error)
        else: # Get all nodes if no filters. This might be too broad.
            query = """
            MATCH (n)
            RETURN n, labels(n) as types LIMIT 100 // Added a limit for safety
            """

        try:
            records = self._execute_query(query, params)
            entities = []
            for record in records:
                node_data = dict(record['n'])
                node_data['id'] = record['n'].element_id # Use element_id
                node_data['types'] = record['types']
                entities.append(node_data)
            return entities
        except Exception as e:
            logger.error(f"Error searching entities (keywords: {keywords}, types: {entity_types}): {e}")
            return []

    def get_entity_neighbors(self, entity_id: str, max_depth: int = 2) -> Dict:
        # Assuming entity_id is the Neo4j element ID.
        # If entity_id is a property like 'name', the MATCH clause needs to be adjusted.
        query = f"""
        MATCH (start_node)
        WHERE elementId(start_node) = $entity_id
        CALL apoc.path.subgraphAll(start_node, {{maxLevel: $max_depth}})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        # This query uses APOC. If APOC is not available, a variable-length path match would be needed:
        # MATCH path = (start_node)-[*1..{max_depth}]-(neighbor)
        # WHERE elementId(start_node) = $entity_id
        # RETURN start_node, collect(DISTINCT neighbor) AS neighbors, collect(DISTINCT relationships(path)) AS rels

        params = {"entity_id": entity_id, "max_depth": max_depth}

        try:
            result = self._execute_query(query, params)
            if not result:
                return {"nodes": [], "relationships": []}

            # Process nodes and relationships from the result
            # APOC subgraphAll returns lists of nodes and relationships
            nodes_data = []
            for node in result[0]['nodes']:
                node_info = dict(node)
                node_info['id'] = node.element_id
                node_info['labels'] = list(node.labels)
                nodes_data.append(node_info)

            rels_data = []
            for rel in result[0]['relationships']:
                rel_info = {
                    "id": rel.element_id,
                    "type": rel.type,
                    "start_node_id": rel.start_node.element_id,
                    "end_node_id": rel.end_node.element_id,
                    "properties": dict(rel)
                }
                rels_data.append(rel_info)

            return {"nodes": nodes_data, "relationships": rels_data}

        except Exception as e:
            # Check if the error is due to APOC not being available
            if "Unknown function 'apoc.path.subgraphAll'" in str(e):
                logger.warning("APOC function 'apoc.path.subgraphAll' not found. Falling back to basic path query for get_entity_neighbors.")
                # Fallback query without APOC
                fallback_query = f"""
                MATCH path = (start_node)-[rels*1..{max_depth}]-(neighbor)
                WHERE elementId(start_node) = $entity_id
                RETURN start_node, collect(DISTINCT neighbor) AS neighbors_nodes, collect(DISTINCT rels) AS path_relationships
                """
                params_fallback = {"entity_id": entity_id} # max_depth is part of the path pattern
                result_fallback = self._execute_query(fallback_query, params_fallback)

                if not result_fallback or not result_fallback[0]['neighbors_nodes']:
                    return {"nodes": [], "relationships": []}

                processed_nodes = {}
                processed_rels = {}

                # Process start node
                start_node_obj = result_fallback[0]['start_node']
                start_node_data = dict(start_node_obj)
                start_node_data['id'] = start_node_obj.element_id
                start_node_data['labels'] = list(start_node_obj.labels)
                processed_nodes[start_node_obj.element_id] = start_node_data

                for record in result_fallback:
                    for node_obj in record['neighbors_nodes']:
                        if node_obj.element_id not in processed_nodes:
                            node_data = dict(node_obj)
                            node_data['id'] = node_obj.element_id
                            node_data['labels'] = list(node_obj.labels)
                            processed_nodes[node_obj.element_id] = node_data

                    for path_rel_list in record['path_relationships']: # list of relationships in a path
                        for rel_obj in path_rel_list:
                             if rel_obj.element_id not in processed_rels:
                                rel_data = {
                                    "id": rel_obj.element_id,
                                    "type": rel_obj.type,
                                    "start_node_id": rel_obj.start_node.element_id,
                                    "end_node_id": rel_obj.end_node.element_id,
                                    "properties": dict(rel_obj)
                                }
                                processed_rels[rel_obj.element_id] = rel_data

                return {
                    "nodes": list(processed_nodes.values()),
                    "relationships": list(processed_rels.values())
                }

            logger.error(f"Error getting entity neighbors for ({entity_id}): {e}")
            return {"nodes": [], "relationships": []}


    def get_graph_statistics(self) -> Dict:
        stats = {}
        try:
            # Get total nodes
            node_count_query = "MATCH (n) RETURN count(n) AS totalNodes"
            result = self._execute_query(node_count_query)
            stats['total_nodes'] = result[0]['totalNodes'] if result else 0

            # Get total relationships
            rel_count_query = "MATCH ()-[r]->() RETURN count(r) AS totalRelationships"
            result = self._execute_query(rel_count_query)
            stats['total_relationships'] = result[0]['totalRelationships'] if result else 0

            # Get node type distribution
            node_type_query = "MATCH (n) RETURN labels(n) AS labels, count(n) AS count"
            result = self._execute_query(node_type_query)
            node_type_distribution = {}
            for record in result:
                # A node can have multiple labels; consider primary label or all
                label_key = ":".join(sorted(record['labels'])) # e.g., "Bridge:SuspensionBridge"
                if label_key:
                    node_type_distribution[label_key] = record['count']
            stats['node_type_distribution'] = node_type_distribution

            # Get relationship type distribution
            rel_type_query = "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count"
            result = self._execute_query(rel_type_query)
            stats['relationship_type_distribution'] = {record['type']: record['count'] for record in result}

            # Graph density (for undirected graph: 2*E / (V*(V-1)) )
            # For directed graph: E / (V*(V-1))
            # Neo4j graphs can have multiple edges between nodes and self-loops, so density calculation can be nuanced.
            # Using the simple directed graph formula for now.
            if stats['total_nodes'] > 1:
                density = stats['total_relationships'] / (stats['total_nodes'] * (stats['total_nodes'] - 1))
                stats['graph_density'] = round(density, 4)
            else:
                stats['graph_density'] = 0 # Or undefined/None

            # Connectivity (e.g., number of weakly connected components)
            # This requires a more complex query, possibly using APOC.
            # Example: CALL gds.wcc.stats('myGraph') YIELD componentCount; (if using GDS library)
            # For a simpler approach, we can check if the graph is connected (1 component) or not.
            # This is a placeholder, as true connectivity analysis is involved.
            try:
                # Attempt to use GDS if available, otherwise skip or use a simpler metric
                # Check for weakly connected components count
                # This query assumes GDS plugin is installed and a graph projection exists or can be made.
                # For a quick check without GDS:
                # MATCH (n) CALL { WITH n MATCH (n)-[*0..]-(m) RETURN count(DISTINCT m) as component_size }
                # RETURN count(DISTINCT n) as num_nodes, sum(component_size) / count(DISTINCT n) as avg_component_size
                # This is not exactly component count.
                # A simple check: is there at least one node?
                # if stats['total_nodes'] > 0:
                #     connected_query = "MATCH (n) WITH n CALL { MATCH p=(n)-[*]-(m) RETURN count(p)>0 AS connected } RETURN count(DISTINCT n) as nodes, sum(CASE WHEN connected THEN 1 ELSE 0 END) as connected_nodes"
                #     # This is also not straightforward.
                # For now, let's add a placeholder or skip advanced connectivity.
                stats['connected_components_count'] = "Not implemented" # Placeholder
            except Exception as e:
                logger.warning(f"Could not calculate connected components: {e}")
                stats['connected_components_count'] = "Error calculating"


            return stats
        except Exception as e:
            logger.error(f"Error getting graph statistics: {e}")
            return {
                "total_nodes": -1, "total_relationships": -1,
                "node_type_distribution": {}, "relationship_type_distribution": {},
                "graph_density": -1, "connected_components_count": "Error"
            }

    # Example usage (can be removed or placed in a test file)
    # if __name__ == '__main__':
    #     service = Neo4jRealService()
    #     try:
            # Test entity creation
            # entity_id1 = service.create_bridge_entity("Bridge", {"name": "Golden Gate Bridge", "length_m": 2737})
            # entity_id2 = service.create_bridge_entity("Location", {"name": "San Francisco"})
            # print(f"Created entity 1: {entity_id1}")
            # print(f"Created entity 2: {entity_id2}")

            # if entity_id1 and entity_id2:
                # Test relationship creation (assuming name is used as ID here)
                # rel_success = service.create_relationship("Golden Gate Bridge", "San Francisco", "LOCATED_IN", {"year_opened": 1937})
                # print(f"Relationship creation successful: {rel_success}")

            # Test search
            # search_results = service.search_entities(keywords=["Golden Gate"], entity_types=["Bridge"])
            # print(f"Search results: {search_results}")

            # Test neighbors (using element ID from search_results if available)
            # if search_results and 'id' in search_results[0]:
            #     element_id_for_neighbors = search_results[0]['id']
            #     neighbors = service.get_entity_neighbors(element_id_for_neighbors)
            #     print(f"Neighbors of {element_id_for_neighbors}: {neighbors}")
            # else:
            #     print("Skipping neighbor search as no suitable entity ID found from search.")

            # Test statistics
            # graph_stats = service.get_graph_statistics()
            # print(f"Graph statistics: {graph_stats}")

    #     finally:
    #         service.close()

# To ensure the logger is configured if this script is run directly (for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Example of how to run (assuming Neo4j is running and configured in .env)
    # settings.NEO4J_URI, settings.NEO4J_USER, settings.NEO4J_PASSWORD should be set

    # This part is for quick, direct testing of the service.
    # In a real application, this would be part of integration tests.
    print("Attempting to initialize Neo4jRealService for a quick test...")
    print(f"Using Neo4j URI: {settings.NEO4J_URI}") # Ensure settings are loaded

    try:
        service = Neo4jRealService()
        print("Neo4jRealService initialized.")

        # Clean up test data before running tests
        print("Cleaning up any existing test data...")
        service._execute_query("MATCH (n {test_marker: 'neo4j_real_service_test'}) DETACH DELETE n")
        print("Test data cleanup complete.")

        # Test entity creation
        print("Testing entity creation...")
        props1 = {"name": "TestBridge1", "type": "Suspension", "test_marker": "neo4j_real_service_test"}
        entity_id1 = service.create_bridge_entity("BridgeTest", props1)
        print(f"Created entity 'TestBridge1' with ID: {entity_id1}")
        assert entity_id1 is not None

        props2 = {"name": "TestLocation1", "city": "TestCity", "test_marker": "neo4j_real_service_test"}
        entity_id2 = service.create_bridge_entity("LocationTest", props2)
        print(f"Created entity 'TestLocation1' with ID: {entity_id2}")
        assert entity_id2 is not None

        # Test relationship creation (using names as identifiers as per current create_relationship)
        print("Testing relationship creation...")
        # To make create_relationship work with names, ensure nodes with these names exist.
        # The create_bridge_entity currently returns elementId.
        # For create_relationship to work with names, we need to ensure the MATCH clause finds them.
        # Let's use the names "TestBridge1" and "TestLocation1"

        rel_success = service.create_relationship("TestBridge1", "TestLocation1", "IS_LOCATED_IN_TEST", {"since": "2023"})
        print(f"Relationship 'IS_LOCATED_IN_TEST' creation successful: {rel_success}")
        assert rel_success

        # Test search entities
        print("Testing entity search...")
        search_results = service.search_entities(keywords=["TestBridge1"], entity_types=["BridgeTest"])
        print(f"Search results for 'TestBridge1': {search_results}")
        assert len(search_results) > 0
        assert search_results[0]['n']['name'] == "TestBridge1"
        retrieved_entity_id_for_neighbors = search_results[0]['id'] # This is elementId

        # Test get entity neighbors (using the elementId from search)
        print(f"Testing get entity neighbors for ID: {retrieved_entity_id_for_neighbors}...")
        neighbors = service.get_entity_neighbors(retrieved_entity_id_for_neighbors, max_depth=1)
        print(f"Neighbors result: {neighbors}")
        assert len(neighbors['nodes']) >= 2 # Should include TestBridge1 and TestLocation1
        assert len(neighbors['relationships']) >= 1

        # Verify neighbor details
        found_bridge = any(n['properties'].get('name') == 'TestBridge1' for n in neighbors['nodes'])
        found_location = any(n['properties'].get('name') == 'TestLocation1' for n in neighbors['nodes'])
        # APOC returns properties inside the node map, not nested. My processing puts them in 'properties'
        # Correcting based on my `get_entity_neighbors` APOC processing:
        found_bridge = any(n.get('name') == 'TestBridge1' for n in neighbors['nodes'])
        found_location = any(n.get('name') == 'TestLocation1' for n in neighbors['nodes'])
        # If using the non-APOC fallback, structure might differ slightly.
        # The APOC path returns nodes with their properties directly. My code wraps them.
        # Let's check the direct output of my function:
        # nodes_data.append(node_info) where node_info = dict(node)
        # So, properties are at the top level of each dict in neighbors['nodes']

        # Re-check based on my node processing in get_entity_neighbors:
        # node_info = dict(node) -> so properties are at the top level.
        # node_info['id'] = node.element_id
        # node_info['labels'] = list(node.labels)
        found_bridge = any(n.get('name') == 'TestBridge1' and 'BridgeTest' in n.get('labels', []) for n in neighbors['nodes'])
        found_location = any(n.get('name') == 'TestLocation1' and 'LocationTest' in n.get('labels', []) for n in neighbors['nodes'])

        assert found_bridge, "TestBridge1 not found in neighbors"
        assert found_location, "TestLocation1 not found in neighbors"


        # Test graph statistics
        print("Testing graph statistics...")
        graph_stats = service.get_graph_statistics()
        print(f"Graph statistics: {graph_stats}")
        assert graph_stats['total_nodes'] >= 2 # Could be more if other data exists
        assert graph_stats['total_relationships'] >= 1
        assert graph_stats['node_type_distribution'].get('BridgeTest', 0) >= 1
        assert graph_stats['relationship_type_distribution'].get('IS_LOCATED_IN_TEST', 0) >= 1

        print("All basic tests for Neo4jRealService passed.")

    except Exception as e:
        print(f"An error occurred during Neo4jRealService testing: {e}")
        logger.exception("Exception during direct test run of Neo4jRealService")
    finally:
        if 'service' in locals() and service.driver:
            # Clean up test data after running tests
            print("Cleaning up test data post-run...")
            service._execute_query("MATCH (n {test_marker: 'neo4j_real_service_test'}) DETACH DELETE n")
            print("Test data cleanup complete.")
            service.close()
            print("Neo4j connection closed.")
