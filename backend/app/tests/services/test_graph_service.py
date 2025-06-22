# backend/app/tests/services/test_graph_service.py
import pytest
from neo4j import Driver
import uuid

from backend.app.services.graph_service import GraphDatabaseService, get_graph_service
from backend.app.db.neo4j_driver import get_neo4j_driver, close_neo4j_driver
from backend.app.models.graph_models import (
    BridgeModel, ComponentModel, MaterialModel, StandardModel,
    RelationshipData
)
from backend.app.core.config import settings

# 全局测试数据
TEST_BRIDGE_ID = f"test-bridge-{uuid.uuid4()}"
TEST_COMPONENT_ID = f"test-component-{uuid.uuid4()}"
TEST_MATERIAL_ID = f"test-material-{uuid.uuid4()}"
TEST_STANDARD_ID = f"test-standard-{uuid.uuid4()}"

# Fixture to manage Neo4j driver and service for tests
@pytest.fixture(scope="session", autouse=True)
def setup_neo4j_driver_for_session():
    # This ensures the driver is initialized once per session using app's config
    # and closed at the end. Tests will use this shared driver.
    # Note: Tests will run against the configured Neo4j instance.
    # For true isolation, a dedicated test DB or Dockerized Neo4j for tests is better.
    try:
        driver = get_neo4j_driver() # Initialize driver from main app logic
        # Optionally, clear test data from previous runs, BE VERY CAREFUL
        # with driver.session(database=settings.NEO4J_DATABASE) as session:
        #     session.run("MATCH (n) WHERE n.id STARTS WITH 'test-' DETACH DELETE n")
        #     print("\nCleared previous test data.")
    except Exception as e:
        pytest.fail(f"Failed to initialize Neo4j driver for tests: {e}")

    yield driver # Provide the driver to the service fixture if needed, or service can get it itself

    # Teardown: close driver after all tests in session are done
    # close_neo4j_driver() # app's main.py shutdown will handle this if tests run within app context
    # For standalone pytest runs, explicit close might be needed if not using app lifecycle.
    # Let's assume for now that the driver is managed globally.
    # If tests run `get_neo4j_driver` themselves, then `close_neo4j_driver` is needed.

@pytest.fixture(scope="function") # Use "function" scope for service if it holds state or for cleanup
def graph_service(setup_neo4j_driver_for_session) -> GraphDatabaseService:
    # The service will use the driver initialized by setup_neo4j_driver_for_session
    # Ensure the service gets a fresh instance or is stateless, or re-initialize.
    # get_graph_service() from service file might return a singleton.
    # For tests, it might be better to instantiate directly if driver is available.
    if setup_neo4j_driver_for_session:
        return GraphDatabaseService(driver=setup_neo4j_driver_for_session)
    else: # Fallback if direct driver injection preferred
        return get_graph_service()


# --- Test Helper Functions ---
def cleanup_test_node(service: GraphDatabaseService, label: str, node_id: str):
    try:
        service.delete_node(label, node_id)
    except Exception: # Ignore if not found, etc.
        pass

# --- Test Cases for GraphDatabaseService ---

def test_create_indexes_and_constraints(graph_service: GraphDatabaseService):
    """测试索引和约束的创建。"""
    results = graph_service.create_indexes_and_constraints()
    assert "Bridge_id_unique" in results
    assert "Component_name_index" in results
    # Check for "initiated" or "already exists" status, avoid "Failed"
    for key, value in results.items():
        assert "Failed" not in value, f"Index/Constraint {key} creation failed: {value}"

# Node CRUD tests
def test_create_and_get_bridge_node(graph_service: GraphDatabaseService):
    """测试创建和获取桥梁节点。"""
    bridge_data = BridgeModel(
        id=TEST_BRIDGE_ID,
        name="Test Bridge Alpha",
        location="Test Location",
        bridge_type="Test Type",
        additional_props={"test_key": "test_value"}
    )
    cleanup_test_node(graph_service, "Bridge", TEST_BRIDGE_ID) # Cleanup before test

    created_node = graph_service.create_node(label="Bridge", node_data=bridge_data)
    assert created_node is not None
    assert created_node["id"] == TEST_BRIDGE_ID
    assert created_node["name"] == "Test Bridge Alpha"
    assert created_node["additional_props"]["test_key"] == "test_value"

    fetched_node = graph_service.get_node_by_id(label="Bridge", node_id=TEST_BRIDGE_ID)
    assert fetched_node is not None
    assert fetched_node["id"] == TEST_BRIDGE_ID
    assert fetched_node["name"] == "Test Bridge Alpha"

    # Test get_nodes_by_label
    all_bridges = graph_service.get_nodes_by_label(label="Bridge", limit=10)
    assert any(b["id"] == TEST_BRIDGE_ID for b in all_bridges)

    cleanup_test_node(graph_service, "Bridge", TEST_BRIDGE_ID) # Cleanup after test

def test_update_node(graph_service: GraphDatabaseService):
    """测试更新节点属性。"""
    comp_data = ComponentModel(id=TEST_COMPONENT_ID, name="Test Component Original")
    cleanup_test_node(graph_service, "Component", TEST_COMPONENT_ID)
    graph_service.create_node(label="Component", node_data=comp_data)

    update_payload = ComponentModel( # Using full model for update schema for simplicity here
        name="Test Component Updated",
        component_type="Updated Type",
        additional_props={"status": "active"}
    )
    # In actual API, this would be ComponentUpdateSchema
    # For service test, we pass the Pydantic model that update_node expects (which is Any)
    # The service layer converts this to dict(exclude_unset=True)

    updated_node = graph_service.update_node(
        label="Component",
        node_id=TEST_COMPONENT_ID,
        node_update_data=update_payload
    )
    assert updated_node is not None
    assert updated_node["name"] == "Test Component Updated"
    assert updated_node["component_type"] == "Updated Type"
    assert updated_node["additional_props"]["status"] == "active"

    # Check that original fields not in update_payload are still there (if any were set)
    # In this case, id should persist. Name is overwritten.
    assert updated_node["id"] == TEST_COMPONENT_ID

    cleanup_test_node(graph_service, "Component", TEST_COMPONENT_ID)

def test_delete_node(graph_service: GraphDatabaseService):
    """测试删除节点。"""
    mat_data = MaterialModel(id=TEST_MATERIAL_ID, name="Test Material to Delete")
    cleanup_test_node(graph_service, "Material", TEST_MATERIAL_ID)
    graph_service.create_node(label="Material", node_data=mat_data)

    was_deleted = graph_service.delete_node(label="Material", node_id=TEST_MATERIAL_ID)
    assert was_deleted is True

    fetched_node = graph_service.get_node_by_id(label="Material", node_id=TEST_MATERIAL_ID)
    assert fetched_node is None

    # Test deleting non-existent node
    was_deleted_again = graph_service.delete_node(label="Material", node_id=TEST_MATERIAL_ID)
    assert was_deleted_again is False


# Relationship CRUD tests
@pytest.fixture(scope="function")
def setup_nodes_for_relationship_test(graph_service: GraphDatabaseService):
    """为关系测试创建起始和结束节点。"""
    bridge = BridgeModel(id=f"{TEST_BRIDGE_ID}-rel", name="BridgeForRelTest")
    component = ComponentModel(id=f"{TEST_COMPONENT_ID}-rel", name="ComponentForRelTest")

    cleanup_test_node(graph_service, "Bridge", bridge.id)
    cleanup_test_node(graph_service, "Component", component.id)

    graph_service.create_node(label="Bridge", node_data=bridge)
    graph_service.create_node(label="Component", node_data=component)

    yield bridge.id, component.id # Provide IDs to the test

    cleanup_test_node(graph_service, "Bridge", bridge.id)
    cleanup_test_node(graph_service, "Component", component.id)


def test_create_and_get_relationship(graph_service: GraphDatabaseService, setup_nodes_for_relationship_test):
    """测试创建和获取关系。"""
    bridge_id, component_id = setup_nodes_for_relationship_test

    rel_data = RelationshipData(
        start_node_label="Bridge", start_node_id=bridge_id,
        end_node_label="Component", end_node_id=component_id,
        rel_type="HAS_COMPONENT_TEST",
        properties={"status": "active_test_rel"}
    )
    created_rel = graph_service.create_relationship(rel_data)
    assert created_rel is not None
    assert created_rel["type"] == "HAS_COMPONENT_TEST"
    assert created_rel["properties"]["status"] == "active_test_rel"
    assert created_rel["start_node_id"] == bridge_id
    assert created_rel["end_node_id"] == component_id

    # Store internal relationship ID if needed for specific deletion test (not used here)
    # rel_internal_id = created_rel["id"]

    relationships = graph_service.get_relationships_of_node(
        node_label="Bridge", node_id=bridge_id, rel_type="HAS_COMPONENT_TEST"
    )
    assert len(relationships) >= 1
    found_rel = next((r for r in relationships if r["end_node_id"] == component_id and r["type"] == "HAS_COMPONENT_TEST"), None)
    assert found_rel is not None
    assert found_rel["properties"]["status"] == "active_test_rel"

    # Test deleting the relationship
    was_rel_deleted = graph_service.delete_relationship(
        start_node_label="Bridge", start_node_id=bridge_id,
        end_node_label="Component", end_node_id=component_id,
        rel_type="HAS_COMPONENT_TEST"
    )
    assert was_rel_deleted is True

    relationships_after_delete = graph_service.get_relationships_of_node(
        node_label="Bridge", node_id=bridge_id, rel_type="HAS_COMPONENT_TEST"
    )
    found_rel_after_delete = next((r for r in relationships_after_delete if r["end_node_id"] == component_id), None)
    assert found_rel_after_delete is None


# Batch import test
def test_batch_import_data(graph_service: GraphDatabaseService):
    """测试批量导入数据。"""
    node_id_batch_b1 = f"test-batch-b1-{uuid.uuid4()}"
    node_id_batch_c1 = f"test-batch-c1-{uuid.uuid4()}"

    # Cleanup before test
    cleanup_test_node(graph_service, "Bridge", node_id_batch_b1)
    cleanup_test_node(graph_service, "Component", node_id_batch_c1)

    import_data = {
        "nodes": [
            {"label": "Bridge", "properties": {"id": node_id_batch_b1, "name": "Batch Bridge 1"}},
            {"label": "Component", "properties": {"id": node_id_batch_c1, "name": "Batch Component 1"}},
        ],
        "relationships": [
            {
                "start_node_label": "Bridge", "start_node_id": node_id_batch_b1,
                "end_node_label": "Component", "end_node_id": node_id_batch_c1,
                "rel_type": "BATCH_HAS_COMPONENT", "properties": {"source": "batch_test"}
            }
        ]
    }
    results = graph_service.batch_import_data(import_data)
    assert not results.get("errors"), f"Batch import failed with errors: {results.get('errors')}"
    # The service currently returns 'nodes_created' which might be 0 if MERGE found existing.
    # Let's check if nodes exist instead.
    # assert results["nodes_created"] == 2
    assert results["relationships_created"] == 1

    b1 = graph_service.get_node_by_id("Bridge", node_id_batch_b1)
    c1 = graph_service.get_node_by_id("Component", node_id_batch_c1)
    assert b1 is not None and b1["name"] == "Batch Bridge 1"
    assert c1 is not None and c1["name"] == "Batch Component 1"

    rels = graph_service.get_relationships_of_node("Bridge", node_id_batch_b1, "BATCH_HAS_COMPONENT")
    assert len(rels) == 1
    assert rels[0]["end_node_id"] == node_id_batch_c1
    assert rels[0]["properties"]["source"] == "batch_test"

    # Cleanup after test
    cleanup_test_node(graph_service, "Bridge", node_id_batch_b1)
    cleanup_test_node(graph_service, "Component", node_id_batch_c1)


# Complex query tests
def test_get_components_of_bridge_complex_query(graph_service: GraphDatabaseService, setup_nodes_for_relationship_test):
    """测试复杂查询: 获取桥梁的构件。"""
    bridge_id, component_id = setup_nodes_for_relationship_test # Uses different IDs due to fixture scope

    # Create a specific relationship for this test
    rel_data = RelationshipData(
        start_node_label="Bridge", start_node_id=bridge_id,
        end_node_label="Component", end_node_id=component_id,
        rel_type="HAS_COMPONENT" # Standard type used by the complex query
    )
    graph_service.create_relationship(rel_data)

    components = graph_service.get_components_of_bridge(bridge_id)
    assert len(components) >= 1
    assert any(c["id"] == component_id for c in components)

    # Cleanup of relationship is handled by setup_nodes_for_relationship_test's node cleanup (DETACH DELETE)

def test_count_nodes_by_label_aggregation(graph_service: GraphDatabaseService):
    """测试节点按标签统计。"""
    # Create a temporary standard node to ensure at least one count is > 0 for Standard
    std_data = StandardModel(id=TEST_STANDARD_ID, name="Test Standard for Counting")
    cleanup_test_node(graph_service, "Standard", TEST_STANDARD_ID)
    graph_service.create_node(label="Standard", node_data=std_data)

    counts = graph_service.count_nodes_by_label_aggregation()
    assert isinstance(counts, list)
    assert len(counts) >= 1 # Should include Bridge, Component, Material, Standard

    standard_count_entry = next((item for item in counts if item["label"] == "Standard"), None)
    assert standard_count_entry is not None
    assert standard_count_entry["count"] >= 1

    cleanup_test_node(graph_service, "Standard", TEST_STANDARD_ID)


# Test for custom query execution (read-only)
def test_execute_custom_read_query(graph_service: GraphDatabaseService):
    """测试执行自定义只读Cypher查询。"""
    # Create a temporary node for the query
    node_id = f"custom-query-node-{uuid.uuid4()}"
    temp_node = ComponentModel(id=node_id, name="Custom Query Test Node")
    cleanup_test_node(graph_service, "Component", node_id)
    graph_service.create_node(label="Component", node_data=temp_node)

    query = "MATCH (c:Component {id: $node_id_param}) RETURN c.name AS name"
    params = {"node_id_param": node_id}
    results = graph_service.execute_custom_query(query, params)

    assert len(results) == 1
    assert results[0]["name"] == "Custom Query Test Node"

    cleanup_test_node(graph_service, "Component", node_id)


# Test for custom write query execution
def test_execute_custom_write_query(graph_service: GraphDatabaseService):
    """测试执行自定义写Cypher查询。"""
    node_id = f"custom-write-node-{uuid.uuid4()}"

    # Ensure node doesn't exist
    cleanup_test_node(graph_service, "Material", node_id)

    query = "CREATE (m:Material {id: $node_id_param, name: $name_param}) RETURN m"
    params = {"node_id_param": node_id, "name_param": "Custom Write Material"}

    summary = graph_service.execute_custom_write_query(query, params)
    assert summary["counters"]["nodes_created"] == 1

    # Verify node was created
    fetched_node = graph_service.get_node_by_id("Material", node_id)
    assert fetched_node is not None
    assert fetched_node["name"] == "Custom Write Material"

    cleanup_test_node(graph_service, "Material", node_id)

# Note: More tests can be added for error conditions, edge cases,
# and other complex queries as needed.
# This set provides basic coverage for core GraphDatabaseService functionalities.
