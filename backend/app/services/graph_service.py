# backend/app/services/graph_service.py
import logging
from typing import List, Dict, Any, Optional
from neo4j import Driver, Session, Transaction, Record, Neo4jError
from backend.app.models.graph_models import (
    NodeModel, BridgeModel, ComponentModel, MaterialModel, StandardModel,
    RelationshipData, NodeResponse # Assuming NodeResponse might be useful
)
from backend.app.core.config import settings
import uuid

logger = logging.getLogger(__name__)

# 辅助函数，将Neo4j Record转换为字典
def record_to_dict(record: Record, key: str = "n") -> Dict[str, Any]:
    """将Neo4j节点Record转换为字典, 保留节点ID和属性。"""
    if record is None or key not in record.data():
        return None
    node_data = record.data()[key]
    # Neo4j Python driver returns element_id for nodes, which is a string.
    # For internal consistency with Pydantic models using 'id', we can use it or map properties['id']
    # We'll assume our nodes always have an 'id' property that is our primary business key.
    # node_id = node_data.element_id # This is Neo4j's internal element_id

    # We will store our business 'id' as a property.
    # The NodeModel Pydantic class has an 'id' field.
    # When creating nodes, we ensure this 'id' property is set.

    # Create a dictionary from node properties
    properties = dict(node_data.items())
    return properties


class GraphDatabaseService:
    """
    服务类，用于处理与Neo4j数据库的交互，包括节点和关系的CRUD操作。
    """
    _driver: Driver

    def __init__(self, driver: Driver):
        if driver is None:
            logger.error("GraphDatabaseService initialized with a None driver.")
            raise ValueError("Neo4j driver cannot be None for GraphDatabaseService")
        self._driver = driver
        self.db_name = settings.NEO4J_DATABASE

    def _execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None, db: Optional[str] = None) -> List[Record]:
        """
        执行给定的Cypher查询并返回结果。
        自动处理会话和事务（针对单个查询）。
        """
        database = db or self.db_name
        try:
            with self._driver.session(database=database) as session:
                result = session.run(query, parameters)
                return list(result) # Consume the result fully
        except Neo4jError as e:
            logger.error(f"Neo4j query failed: {query} | params: {parameters} | error: {e}")
            raise  # Re-raise the exception to be handled by the caller or FastAPI error handlers
        except Exception as e:
            logger.error(f"An unexpected error occurred during query execution: {e}")
            raise

    def _execute_write_transaction(self, txc_function, db: Optional[str] = None) -> Any:
        """
        在托管事务中执行写操作。
        txc_function: 一个接收事务对象 (neo4j.Transaction) 作为参数的函数。
        """
        database = db or self.db_name
        try:
            with self._driver.session(database=database) as session:
                return session.write_transaction(txc_function)
        except Neo4jError as e:
            logger.error(f"Neo4j write transaction failed: {e}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during write transaction: {e}")
            raise

    # --- 索引和约束 ---
    def create_indexes_and_constraints(self) -> Dict[str, str]:
        """
        为知识图谱中的节点类型创建推荐的索引和约束。
        确保节点ID的唯一性，并为常用查询属性创建索引。
        """
        results = {}

        # 唯一性约束 (会自动创建关联的索引)
        constraints_queries = {
            "Bridge_id_unique": "CREATE CONSTRAINT IF NOT EXISTS FOR (b:Bridge) REQUIRE b.id IS UNIQUE",
            "Component_id_unique": "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
            "Material_id_unique": "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Material) REQUIRE m.id IS UNIQUE",
            "Standard_id_unique": "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Standard) REQUIRE s.id IS UNIQUE",
        }

        # 额外的索引 (例如，在name属性上)
        indexes_queries = {
            "Bridge_name_index": "CREATE INDEX IF NOT EXISTS FOR (b:Bridge) ON (b.name)",
            "Component_name_index": "CREATE INDEX IF NOT EXISTS FOR (c:Component) ON (c.name)",
            "Material_name_index": "CREATE INDEX IF NOT EXISTS FOR (m:Material) ON (m.name)",
            "Standard_name_index": "CREATE INDEX IF NOT EXISTS FOR (s:Standard) ON (s.name)",
        }

        logger.info("Attempting to create Neo4j constraints...")
        for name, query in constraints_queries.items():
            try:
                self._execute_query(query)
                results[name] = "Constraint creation initiated (or already exists)."
                logger.info(f"Successfully initiated/verified constraint: {name}")
            except Neo4jError as e:
                results[name] = f"Failed to create constraint: {e}"
                logger.error(f"Failed to create constraint {name}: {e}")
            except Exception as e:
                results[name] = f"Unexpected error for constraint {name}: {e}"
                logger.error(f"Unexpected error for constraint {name}: {e}")


        logger.info("Attempting to create Neo4j indexes...")
        for name, query in indexes_queries.items():
            try:
                self._execute_query(query)
                results[name] = "Index creation initiated (or already exists)."
                logger.info(f"Successfully initiated/verified index: {name}")
            except Neo4jError as e:
                results[name] = f"Failed to create index: {e}"
                logger.error(f"Failed to create index {name}: {e}")
            except Exception as e:
                results[name] = f"Unexpected error for index {name}: {e}"
                logger.error(f"Unexpected error for index {name}: {e}")

        return results

    # --- 节点 CRUD 操作 ---

    def _create_node_tx(self, tx: Transaction, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """事务函数：创建单个节点。"""
        # 确保节点有一个 'id' 属性，如果Pydantic模型中没有默认生成的话
        if 'id' not in properties or properties['id'] is None:
            properties['id'] = str(uuid.uuid4())

        # Cypher query: CREATE (n:Label $props) RETURN n
        # Using SET for properties is often more robust if properties might be complex
        # MERGE can be used if you want to get or create, but for pure creation, CREATE is fine.
        # query = f"CREATE (n:{label} $properties) RETURN n" # This works if properties is flat

        # More robust: CREATE (n:Label) SET n = $properties RETURN n
        # This handles nested properties better if $properties is a map.
        query = f"CREATE (n:{label}) SET n = $props RETURN n"

        result = tx.run(query, props=properties)
        record = result.single()
        if record:
            return record_to_dict(record, "n")
        return None

    def create_node(self, label: str, node_data: NodeModel) -> Optional[Dict[str, Any]]:
        """
        创建一个带有给定标签和属性的新节点。
        node_data: Pydantic模型实例 (e.g., BridgeModel, ComponentModel).
        返回创建的节点属性字典，如果失败则返回None。
        """
        if not label or not isinstance(label, str):
            raise ValueError("Node label must be a non-empty string.")
        if not isinstance(node_data, NodeModel): # Or more specific types if needed
            raise ValueError("node_data must be an instance of a Pydantic model inheriting from NodeModel.")

        # Pydantic model's .dict() or .model_dump() (v2) can be used to get properties
        # Ensure 'id' is present, NodeModel's default_factory should handle this.
        # properties = node_data.model_dump(exclude_none=True) # Pydantic V2
        properties = node_data.dict(exclude_none=True) # Pydantic V1

        try:
            created_node_props = self._execute_write_transaction(
                lambda tx: self._create_node_tx(tx, label, properties)
            )
            if created_node_props:
                logger.info(f"Node created with label '{label}' and ID '{created_node_props.get('id')}'.")
                return created_node_props
            else:
                logger.warning(f"Node creation attempt for label '{label}' did not return a node.")
                return None
        except Neo4jError as e:
            # Specific error handling, e.g., for constraint violations
            if "already exists" in str(e).lower(): # Basic check for unique constraint error
                logger.error(f"Failed to create node with label '{label}' and ID '{properties.get('id')}': Node with this ID likely already exists. Error: {e}")
                # Depending on requirements, you might want to raise a custom "AlreadyExistsError"
                raise ValueError(f"Node with ID '{properties.get('id')}' already exists.") from e
            logger.error(f"Failed to create node with label '{label}': {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating node with label '{label}': {e}")
            raise

    def get_node_by_id(self, label: str, node_id: str) -> Optional[Dict[str, Any]]:
        """
        通过ID获取特定标签的节点。
        """
        if not label or not isinstance(label, str):
            raise ValueError("Node label must be a non-empty string.")
        if not node_id or not isinstance(node_id, str):
            raise ValueError("Node ID must be a non-empty string.")

        query = f"MATCH (n:{label} {{id: $node_id}}) RETURN n"
        parameters = {"node_id": node_id}

        records = self._execute_query(query, parameters)
        if records and records[0]:
            return record_to_dict(records[0], "n")
        logger.info(f"Node with label '{label}' and ID '{node_id}' not found.")
        return None

    def get_nodes_by_label(self, label: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取指定标签的所有节点，支持分页。
        """
        if not label or not isinstance(label, str):
            raise ValueError("Node label must be a non-empty string.")

        query = f"MATCH (n:{label}) RETURN n SKIP $skip LIMIT $limit"
        parameters = {"skip": skip, "limit": limit}

        records = self._execute_query(query, parameters)
        return [record_to_dict(record, "n") for record in records if record]

    def _update_node_tx(self, tx: Transaction, label: str, node_id: str, properties_to_update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """事务函数：更新节点。"""
        if not properties_to_update:
            # If nothing to update, we could fetch and return the node, or signal no-op
            # For now, let's assume an update implies some change.
            # Fetch and return current state if no props given might be better.
            get_query = f"MATCH (n:{label} {{id: $node_id}}) RETURN n"
            result = tx.run(get_query, node_id=node_id)
            record = result.single()
            return record_to_dict(record, "n") if record else None

        # Cypher: MATCH (n:Label {id: $node_id}) SET n += $props_to_update RETURN n
        # Using += allows partial updates. If you want to overwrite all non-id properties, use SET n = $new_props
        query = f"MATCH (n:{label} {{id: $node_id}}) SET n += $props_to_update RETURN n"

        result = tx.run(query, node_id=node_id, props_to_update=properties_to_update)
        record = result.single()
        return record_to_dict(record, "n") if record else None

    def update_node(self, label: str, node_id: str, node_update_data: Any) -> Optional[Dict[str, Any]]:
        """
        更新具有给定ID的节点的属性。
        node_update_data: Pydantic模型实例 (e.g., BridgeUpdateSchema) containing fields to update.
        ID和标签不可通过此方法更改。
        """
        if not label or not isinstance(label, str):
            raise ValueError("Node label must be a non-empty string.")
        if not node_id or not isinstance(node_id, str):
            raise ValueError("Node ID must be a non-empty string.")

        # Convert Pydantic model to dict, excluding unset fields to only update provided values
        properties_to_update = node_update_data.dict(exclude_unset=True) # Pydantic V1
        # properties_to_update = node_update_data.model_dump(exclude_unset=True) # Pydantic V2

        if 'id' in properties_to_update: # ID should not be updatable here
            del properties_to_update['id']
        if 'label' in properties_to_update: # Label should not be updatable here
            del properties_to_update['label']

        if not properties_to_update:
            logger.info(f"No properties provided to update for node '{label}' with ID '{node_id}'. Returning current state.")
            # Optionally, fetch and return the current node state or return None/raise error
            return self.get_node_by_id(label, node_id)

        updated_node_props = self._execute_write_transaction(
            lambda tx: self._update_node_tx(tx, label, node_id, properties_to_update)
        )

        if updated_node_props:
            logger.info(f"Node '{label}' with ID '{node_id}' updated successfully.")
        else:
            logger.warning(f"Node '{label}' with ID '{node_id}' not found for update or update failed.")
        return updated_node_props

    def _delete_node_tx(self, tx: Transaction, label: str, node_id: str) -> bool:
        """事务函数：删除节点。"""
        # DETACH DELETE removes the node and its relationships.
        # If you want to prevent deletion if relationships exist, use DELETE without DETACH (will error).
        query = f"MATCH (n:{label} {{id: $node_id}}) DETACH DELETE n RETURN count(n) as deleted_count"
        result = tx.run(query, node_id=node_id)
        record = result.single()
        return record and record["deleted_count"] > 0

    def delete_node(self, label: str, node_id: str) -> bool:
        """
        通过ID删除特定标签的节点及其所有关系。
        返回True如果节点被删除，否则False。
        """
        if not label or not isinstance(label, str):
            raise ValueError("Node label must be a non-empty string.")
        if not node_id or not isinstance(node_id, str):
            raise ValueError("Node ID must be a non-empty string.")

        was_deleted = self._execute_write_transaction(
            lambda tx: self._delete_node_tx(tx, label, node_id)
        )

        if was_deleted:
            logger.info(f"Node '{label}' with ID '{node_id}' and its relationships deleted successfully.")
        else:
            logger.warning(f"Node '{label}' with ID '{node_id}' not found for deletion or delete operation failed.")
        return was_deleted

    # --- 关系 CRUD 操作 ---

    def _create_relationship_tx(self, tx: Transaction,
                               start_node_label: str, start_node_id: str,
                               end_node_label: str, end_node_id: str,
                               rel_type: str, properties: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """事务函数：创建关系。"""
        if properties is None:
            properties = {}

        # MERGE is often used for relationships to avoid duplicates if properties are the same.
        # CREATE will always create a new one.
        # For this example, let's use CREATE as we might want multiple relationships of the same type
        # if their properties differ or if the business logic allows it.
        # If relationships should be unique based on type and nodes, MERGE is better.
        # Example with MERGE:
        # query = (
        #     f"MATCH (a:{start_node_label} {{id: $start_id}}), (b:{end_node_label} {{id: $end_id}}) "
        #     f"MERGE (a)-[r:{rel_type}]->(b) " # Basic merge, no properties
        #     f"ON CREATE SET r = $props " # Set properties if relationship is created
        #     f"ON MATCH SET r += $props " # Update properties if relationship exists (optional)
        #     f"RETURN type(r) as type, r as properties, elementId(r) as rel_id, "
        #     f"elementId(startNode(r)) as start_node_element_id, elementId(endNode(r)) as end_node_element_id"
        # )

        # Using CREATE for simplicity, assuming multiple rels of same type are allowed or handled by client logic
        query = (
            f"MATCH (a:{start_node_label} {{id: $start_id}}), (b:{end_node_label} {{id: $end_id}}) "
            f"CREATE (a)-[r:{rel_type} $props]->(b) "
            f"RETURN type(r) as type, r {{.*, elementId: elementId(r), startNodeId: a.id, endNodeId: b.id}} as relationship_data"
        )

        parameters = {
            "start_id": start_node_id,
            "end_id": end_node_id,
            "props": properties
        }
        result = tx.run(query, parameters)
        record = result.single()

        if record and record["relationship_data"]:
            # Neo4j's elementId() is the internal ID.
            # We're adding startNodeId and endNodeId from our domain model for clarity in response.
            rel_data = dict(record["relationship_data"]) # Convert Relationship object to dict
            rel_data_transformed = {
                "id": rel_data.pop("elementId"), # Neo4j internal element ID
                "type": record["type"],
                "start_node_id": rel_data.pop("startNodeId"),
                "end_node_id": rel_data.pop("endNodeId"),
                "properties": rel_data # Remaining items are properties
            }
            return rel_data_transformed
        return None

    def create_relationship(self, rel_data: RelationshipData) -> Optional[Dict[str, Any]]:
        """
        在两个现有节点之间创建一条关系。
        rel_data: RelationshipData Pydantic model instance.
        """
        created_rel = self._execute_write_transaction(
            lambda tx: self._create_relationship_tx(tx,
                                                    rel_data.start_node_label, rel_data.start_node_id,
                                                    rel_data.end_node_label, rel_data.end_node_id,
                                                    rel_data.rel_type, rel_data.properties)
        )
        if created_rel:
            logger.info(f"Relationship '{rel_data.rel_type}' created from "
                        f"({rel_data.start_node_label} {{id: {rel_data.start_node_id}}}) to "
                        f"({rel_data.end_node_label} {{id: {rel_data.end_node_id}}}).")
        else:
            logger.warning(f"Failed to create relationship '{rel_data.rel_type}' or one of the nodes not found.")
        return created_rel

    def get_relationships_of_node(self, node_label: str, node_id: str, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取一个节点的所有（或特定类型）的关系。
        Returns a list of relationship details.
        """
        # Build the relationship pattern part of the query dynamically
        rel_pattern = f"-[r{':' + rel_type if rel_type else ''}]-"

        query = (
            f"MATCH (n:{node_label} {{id: $node_id}}){rel_pattern}(m) "
            f"RETURN type(r) as type, r {{.*, elementId: elementId(r)}} as properties, "
            f"n.id as start_node_id, m.id as end_node_id, labels(m) as end_node_labels"
        )
        # This query returns outgoing relationships. For both incoming and outgoing, match (n)-[r]-(m)
        # For specific direction: (n)-[r]->(m) or (n)<-[r]-(m)

        parameters = {"node_id": node_id}
        records = self._execute_query(query, parameters)

        relationships = []
        for record in records:
            props = dict(record["properties"])
            rel_id = props.pop("elementId") # Neo4j internal element ID
            relationships.append({
                "id": rel_id,
                "type": record["type"],
                "start_node_id": record["start_node_id"],
                "end_node_id": record["end_node_id"],
                "end_node_labels": record["end_node_labels"],
                "properties": props
            })
        return relationships

    def delete_relationship(self, start_node_label: str, start_node_id: str,
                            end_node_label: str, end_node_id: str,
                            rel_type: str) -> bool:
        """
        删除两个特定节点之间的特定类型的关系。
        Note: This deletes ONE such relationship if multiple exist.
        To delete all matching: modify query or loop.
        This simple version assumes there's at most one or you want to delete one.
        """
        def _tx_delete_relationship(tx, s_label, s_id, e_label, e_id, r_type):
            query = (
                f"MATCH (a:{s_label} {{id: $s_id}})-[r:{r_type}]->(b:{e_label} {{id: $e_id}}) "
                f"DELETE r " # Delete the first one found
                f"RETURN count(r) as deleted_count" # This won't actually return count because r is deleted before return
            )
            # A better way to confirm deletion is to try to match again, or rely on query not erroring
            # For now, we assume if query runs and nodes exist, one rel is deleted.
            # To make it safer, we can use a subquery or check existence first.

            # A more robust way to count deletions (if needed, usually not for single delete):
            # Find the relationship first, get its ID, then delete by ID.
            # Or, use this query which attempts to delete and relies on summary.

            # Simpler:
            query_find_and_delete = (
                f"MATCH (a:{s_label} {{id: $s_id}})-[r:{r_type}]->(b:{e_label} {{id: $e_id}}) "
                f"WITH r LIMIT 1 " # Ensure only one relationship is targeted if multiple exist
                f"DELETE r"
            )
            # The summary of the result will indicate if changes were made.
            # result.summary().counters.relationships_deleted
            result = tx.run(query_find_and_delete, s_id=s_id, e_id=e_id)
            return result.summary().counters.relationships_deleted > 0

        was_deleted = self._execute_write_transaction(
            lambda tx: _tx_delete_relationship(tx, start_node_label, start_node_id,
                                               end_node_label, end_node_id, rel_type)
        )

        if was_deleted:
            logger.info(f"Relationship '{rel_type}' between ({start_node_label} {{id: {start_node_id}}}) "
                        f"and ({end_node_label} {{id: {end_node_id}}}) deleted.")
        else:
            logger.warning(f"Relationship '{rel_type}' not found or not deleted.")
        return was_deleted

    # --- Batch and Complex Operations ---

    def batch_import_data(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        批量导入节点和关系数据。
        'data' should be a dictionary like:
        {
            "nodes": [
                {"label": "Bridge", "properties": {"id": "b1", "name": "Bridge1", ...}},
                {"label": "Component", "properties": {"id": "c1", "name": "Comp1", ...}}
            ],
            "relationships": [
                {"start_node_label": "Bridge", "start_node_id": "b1",
                 "end_node_label": "Component", "end_node_id": "c1",
                 "rel_type": "HAS_COMPONENT", "properties": {}}, ...
            ]
        }
        Uses UNWIND for efficient batch creation.
        """
        nodes_to_create = data.get("nodes", [])
        rels_to_create = data.get("relationships", [])

        results = {"nodes_created": 0, "relationships_created": 0, "errors": []}

        # Batch create nodes
        if nodes_to_create:
            # We need to ensure 'id' is present in each node's properties.
            for node_spec in nodes_to_create:
                if 'id' not in node_spec.get('properties', {}):
                    node_spec.setdefault('properties', {})['id'] = str(uuid.uuid4())

            # Group nodes by label for UNWIND query (optional optimization, can also do one UNWIND for all nodes)
            # For simplicity, one UNWIND for all nodes with dynamic labels (requires APOC or careful Cypher)
            # Or, iterate and call create_node (less efficient for large batches)

            # Simpler approach: iterate and call create_node for smaller batches, or use one UNWIND per label type.
            # Using UNWIND for a list of maps, each map containing label and properties:
            # This is more complex if labels are dynamic within the same UNWIND.
            # A common pattern is to UNWIND a list of property maps and use a fixed label.
            # e.g., $nodes = [{"id":"b1", "name":"Bridge1"}, {"id":"b2", "name":"Bridge2"}]
            # UNWIND $nodes AS node_props CREATE (n:Bridge) SET n = node_props

            # For mixed labels, it's often easier to group by label first.
            nodes_by_label = {}
            for node_spec in nodes_to_create:
                label = node_spec["label"]
                nodes_by_label.setdefault(label, []).append(node_spec["properties"])

            def _tx_batch_create_nodes(tx, nodes_map):
                count = 0
                for label, props_list in nodes_map.items():
                    if props_list:
                        # Ensure all nodes have an 'id'
                        for props_item in props_list:
                            if 'id' not in props_item:
                                props_item['id'] = str(uuid.uuid4())

                        # Using MERGE to avoid errors if nodes already exist by ID.
                        # If strict creation is needed and duplicates should error, use CREATE.
                        query = f"UNWIND $props_list AS props MERGE (n:{label} {{id: props.id}}) SET n += props"
                        # SET n = props would overwrite, SET n += props updates/adds.
                        # If using MERGE, ON CREATE SET might be more appropriate for initial values.
                        # For now, MERGE with SET n += props is a common idempotent pattern.
                        summary = tx.run(query, props_list=props_list).summary()
                        count += summary.counters.nodes_created
                return count

            try:
                created_count = self._execute_write_transaction(lambda tx: _tx_batch_create_nodes(tx, nodes_by_label))
                results["nodes_created"] = created_count
                logger.info(f"Batch node import: {created_count} nodes processed/created.")
            except Exception as e:
                logger.error(f"Error during batch node import: {e}")
                results["errors"].append(f"Node import error: {str(e)}")


        # Batch create relationships
        if rels_to_create and not results["errors"]: # Proceed if node import was okay
            # $rels = [{"start_id":"b1", "end_id":"c1", "rel_type":"HAS_COMPONENT", "props":{}}, ...]
            # UNWIND $rels AS rel_spec
            # MATCH (a {id: rel_spec.start_id}), (b {id: rel_spec.end_id})
            # CREATE (a)-[r:DYNAMIC_TYPE_FROM_rel_spec.rel_type]->(b) SET r = rel_spec.props
            # Dynamic relationship types are tricky with plain Cypher UNWIND.
            # Usually, you'd group by rel_type or use APOC.

            # Simplified: group by rel_type, start_label, end_label
            rels_grouped = {}
            for rel_spec in rels_to_create:
                key = (rel_spec["start_node_label"], rel_spec["rel_type"], rel_spec["end_node_label"])
                rels_grouped.setdefault(key, []).append({
                    "start_id": rel_spec["start_node_id"],
                    "end_id": rel_spec["end_node_id"],
                    "properties": rel_spec.get("properties", {})
                })

            def _tx_batch_create_rels(tx, grouped_rels_map):
                count = 0
                for key_tuple, rel_props_list in grouped_rels_map.items():
                    s_label, r_type, e_label = key_tuple
                    if rel_props_list:
                        # MERGE can be used here too if relationships need to be idempotent.
                        query = (
                            f"UNWIND $rel_list AS rel_data "
                            f"MATCH (a:{s_label} {{id: rel_data.start_id}}), (b:{e_label} {{id: rel_data.end_id}}) "
                            f"CREATE (a)-[r:{r_type}]->(b) SET r = rel_data.properties"
                            # Using CREATE. For MERGE:
                            # f"MERGE (a)-[r:{r_type}]->(b) SET r += rel_data.properties" (careful with list properties)
                        )
                        summary = tx.run(query, rel_list=rel_props_list).summary()
                        count += summary.counters.relationships_created
                return count

            try:
                created_count = self._execute_write_transaction(lambda tx: _tx_batch_create_rels(tx, rels_grouped))
                results["relationships_created"] = created_count
                logger.info(f"Batch relationship import: {created_count} relationships processed/created.")
            except Exception as e:
                logger.error(f"Error during batch relationship import: {e}")
                results["errors"].append(f"Relationship import error: {str(e)}")

        return results

    # --- Custom Cypher Execution ---
    def execute_custom_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Executes an arbitrary Cypher query and returns results.
        This is powerful but should be used cautiously (e.g., for read-only queries from trusted sources).
        The result records are converted to dictionaries.
        """
        logger.info(f"Executing custom query: {query[:100]}... with params: {parameters}")

        # For write queries, it's better to use a dedicated method that uses write_transaction.
        # This generic one uses _execute_query which might use implicit transactions for reads.
        # If this is meant for reads:
        records = self._execute_query(query, parameters)

        # Convert records to a list of dicts. This is a generic conversion.
        # Each record can have multiple fields.
        results = []
        for record in records:
            results.append(dict(record.items())) # Converts a Record to a dict of its fields
        return results

    def execute_custom_write_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes an arbitrary Cypher write query using a managed transaction.
        Returns the query summary.
        """
        logger.info(f"Executing custom write query: {query[:100]}... with params: {parameters}")

        def _tx_custom_write(tx, q, p):
            result = tx.run(q, p)
            return result.summary()

        summary = self._execute_write_transaction(lambda tx: _tx_custom_write(tx, query, parameters))

        return {
            "counters": dict(summary.counters),
            "query_type": summary.query_type,
            "plan": summary.plan is not None, # True if plan info is available
            "profile": summary.profile is not None, # True if profile info is available
        }

    # --- Graph Structure Validation and Cleanup (Conceptual) ---
    def validate_graph_structure(self) -> Dict[str, Any]:
        """
        Placeholder for graph validation logic.
        E.g., check for orphaned nodes of certain types, ensure components are linked to bridges, etc.
        Returns a summary of validation results.
        """
        # Example: Find components not connected to any bridge
        # query_orphaned_components = (
        #   "MATCH (c:Component) WHERE NOT (c)<-[:HAS_COMPONENT]-(:Bridge) RETURN count(c) as orphaned_components_count"
        # )
        # ... more validation queries
        logger.warning("Graph structure validation is conceptual and not fully implemented.")
        return {"status": "Validation not fully implemented."}

    def cleanup_graph(self) -> Dict[str, Any]:
        """
        Placeholder for graph cleanup operations.
        E.g., remove orphaned nodes, inconsistent data.
        Use with caution.
        """
        # Example: Delete orphaned components (use carefully!)
        # query_delete_orphaned = (
        #    "MATCH (c:Component) WHERE NOT (c)<-[:HAS_COMPONENT]-(:Bridge) DETACH DELETE c"
        # )
        logger.warning("Graph cleanup is conceptual and not fully implemented. Perform such operations with extreme care.")
        return {"status": "Cleanup not fully implemented."}

    # --- Version Control and Migration Support (Conceptual) ---
    # This would typically involve external tools or a framework like Liquibase for Neo4j,
    # or custom scripts to manage schema versions and data migrations.
    # For now, this is out of scope for direct implementation in GraphDatabaseService.
    def get_schema_version(self) -> str:
        # Potentially query a special :SchemaVersion node
        logger.warning("Schema versioning is conceptual.")
        return "N/A"

    def apply_migration(self, migration_script: str) -> bool:
        # Execute a Cypher script for migration
        logger.warning("Migration support is conceptual.")
        try:
            # self.execute_custom_write_query(migration_script) # Be very careful
            return True
        except Exception:
            return False

    # --- Complex Queries and Domain-Specific Patterns ---

    def get_components_of_bridge(self, bridge_id: str) -> List[Dict[str, Any]]:
        """
        查找特定桥梁的所有构件。
        假设关系为 Bridge -[:HAS_COMPONENT]-> Component
        """
        query = (
            "MATCH (b:Bridge {id: $bridge_id})-[:HAS_COMPONENT]->(c:Component) "
            "RETURN c"
        )
        parameters = {"bridge_id": bridge_id}
        records = self._execute_query(query, parameters)
        return [record_to_dict(record, "c") for record in records if record]

    def get_components_by_material(self, material_id: str) -> List[Dict[str, Any]]:
        """
        查找使用特定材料的所有构件。
        假设关系为 Component -[:MADE_OF]-> Material
        """
        query = (
            "MATCH (c:Component)-[:MADE_OF]->(m:Material {id: $material_id}) "
            "RETURN c"
        )
        parameters = {"material_id": material_id}
        records = self._execute_query(query, parameters)
        return [record_to_dict(record, "c") for record in records if record]

    def get_elements_following_standard(self, standard_id: str, element_label: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查找遵循特定标准的所有元素（桥梁或构件）。
        如果提供了 element_label (e.g., "Bridge", "Component")，则只查找该类型的元素。
        假设关系为 Element -[:FOLLOWS_SPEC]-> Standard
        """
        if element_label and element_label not in ["Bridge", "Component"]: # Add other valid types if necessary
            raise ValueError("Invalid element_label. Must be 'Bridge', 'Component', or None.")

        node_match = f"(elem{':' + element_label if element_label else ''})" # Matches (elem) or (elem:Bridge)

        query = (
            f"MATCH {node_match}-[:FOLLOWS_SPEC]->(s:Standard {{id: $standard_id}}) "
            "RETURN elem, labels(elem) as elem_labels"
        )
        parameters = {"standard_id": standard_id}
        records = self._execute_query(query, parameters)

        results = []
        for record in records:
            if record and "elem" in record:
                elem_data = record_to_dict(record, "elem")
                elem_data["labels"] = record["elem_labels"] # Add labels to the result
                results.append(elem_data)
        return results

    def count_nodes_by_label_aggregation(self) -> List[Dict[str, Any]]:
        """
        聚合统计：计算每种已知节点标签（Bridge, Component, Material, Standard）的数量。
        """
        # This is a bit manual. For fully dynamic labels: CALL db.labels() YIELD label MATCH (n) WHERE label IN labels(n) ...
        # For known set of labels:
        queries = {
            "Bridge": "MATCH (n:Bridge) RETURN count(n) as count",
            "Component": "MATCH (n:Component) RETURN count(n) as count",
            "Material": "MATCH (n:Material) RETURN count(n) as count",
            "Standard": "MATCH (n:Standard) RETURN count(n) as count",
        }
        results = []
        for label, query in queries.items():
            try:
                record = self._execute_query(query)
                if record and record[0]:
                    results.append({"label": label, "count": record[0]["count"]})
            except Exception as e:
                logger.error(f"Error counting nodes for label {label}: {e}")
                results.append({"label": label, "count": -1, "error": str(e)}) # Indicate error
        return results

    def find_connection_paths_between_components(self, start_component_id: str, end_component_id: str, max_hops: int = 5) -> List[List[Dict[str, Any]]]:
        """
        查找两个构件之间的连接路径 (通过 :CONNECTED_TO 关系)。
        Returns a list of paths, where each path is a list of node properties.
        max_hops: 限制路径的最大长度以避免无限循环或过长的查询。
        """
        if max_hops <= 0:
            raise ValueError("max_hops must be a positive integer.")

        query = (
            f"MATCH path = (start_c:Component {{id: $start_id}})-[:CONNECTED_TO*1..{max_hops}]->(end_c:Component {{id: $end_id}}) "
            "RETURN path"
        )
        # For undirected paths: -[:CONNECTED_TO*1..{max_hops}]-
        # The query above finds directed paths.

        parameters = {"start_id": start_component_id, "end_id": end_component_id}
        records = self._execute_query(query, parameters)

        paths_result = []
        for record in records:
            path_obj = record["path"] # This is a neo4j.graph.Path object
            current_path_nodes = []
            for node in path_obj.nodes:
                # Convert Neo4j Node object to dictionary
                # We need the label to properly parse it if we have different node types in path
                # For now, assume all nodes in CONNECTED_TO path are Components
                node_props = dict(node.items())
                # node_props['labels'] = list(node.labels) # Add labels if needed
                current_path_nodes.append(node_props)
            paths_result.append(current_path_nodes)
        return paths_result

    def get_bridge_components_by_material(self, bridge_id: str, material_id: str) -> List[Dict[str, Any]]:
        """
        多跳查询：查找特定桥梁的所有使用特定材料的构件。
        Path: Bridge -[:HAS_COMPONENT]-> Component -[:MADE_OF]-> Material
        """
        query = (
            "MATCH (b:Bridge {id: $bridge_id})-[:HAS_COMPONENT]->(c:Component)-[:MADE_OF]->(m:Material {id: $material_id}) "
            "RETURN c"
        )
        parameters = {"bridge_id": bridge_id, "material_id": material_id}
        records = self._execute_query(query, parameters)
        return [record_to_dict(record, "c") for record in records if record]


# Helper to get the service instance with the driver
# This would typically be part of a dependency injection system in a FastAPI app.
# For now, it's a simple helper.
_graph_db_service_instance: Optional[GraphDatabaseService] = None

def get_graph_service(driver: Optional[Driver] = None) -> GraphDatabaseService:
    """
    Provides a singleton instance of the GraphDatabaseService.
    If a driver is provided, it can be used to re-initialize (e.g., for tests).
    In a FastAPI app, the driver would be managed globally and passed at app startup.
    """
    global _graph_db_service_instance
    if _graph_db_service_instance is None or driver is not None:
        if driver is None:
            # This import should be at the top, but for this helper structure:
            from backend.app.db.neo4j_driver import get_neo4j_driver
            try:
                driver = get_neo4j_driver()
            except ConnectionError as e:
                logger.error(f"Failed to get Neo4j driver for GraphService: {e}")
                raise  # Propagate error if driver can't be obtained

        if driver is None: # Still None after trying to get it
             raise RuntimeError("Neo4j driver is not available, cannot create GraphDatabaseService.")

        _graph_db_service_instance = GraphDatabaseService(driver)
        logger.info("GraphDatabaseService instance created/re-initialized.")
    return _graph_db_service_instance

# Example of how it might be used in an API endpoint (FastAPI):
# from fastapi import Depends
# from backend.app.db.neo4j_driver import get_neo4j_driver_di # Assuming a DI function for driver
#
# @router.post("/nodes/{label}")
# async def api_create_node(label: str, node_data: BridgeModel, # Example, use appropriate model
#                           driver: Driver = Depends(get_neo4j_driver_di)):
#     service = GraphDatabaseService(driver) # Or get_graph_service() if it uses a global driver
#     created = service.create_node(label, node_data)
#     if not created:
#         raise HTTPException(status_code=500, detail="Failed to create node")
#     return created
