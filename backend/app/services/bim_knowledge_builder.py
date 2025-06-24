from typing import Dict, List
# Assuming the services are in the same directory or accessible via Python's import system.
# If they are in backend/app/services/, and this file is also there, direct imports should work.
# Otherwise, adjust the import path e.g., backend.app.services.ifc_parser_service
try:
    from .ifc_parser_service import IFCParserService
    from .bridge_bim_analyzer import BridgeBIMAnalyzer
except ImportError: # Fallback for cases where the script might be run directly or module structure is different
    from ifc_parser_service import IFCParserService
    from bridge_bim_analyzer import BridgeBIMAnalyzer

class BIMKnowledgeBuilder:
    def __init__(self):
        self.ifc_parser = IFCParserService()
        self.bim_analyzer = BridgeBIMAnalyzer()

    def build_knowledge_from_bim(self, file_path: str) -> Dict:
        """
        Builds a knowledge graph from a BIM model.
        1. Parses IFC file.
        2. Analyzes bridge components.
        3. Extracts design parameters.
        4. Constructs knowledge nodes and relationships.
        """
        # 1. Parse IFC file
        # The parse_ifc_file method in IFCParserService returns a dictionary with keys:
        # "metadata", "spatial_structure", "building_elements",
        # "materials_and_properties", "geometric_representations"
        parsed_ifc_data = self.ifc_parser.parse_ifc_file(file_path)

        if not parsed_ifc_data or parsed_ifc_data.get("metadata", {}).get("error"):
            error_message = parsed_ifc_data.get("metadata", {}).get("error", "Failed to parse IFC file.")
            return {"nodes": [], "relationships": [], "error": error_message}

        building_elements = parsed_ifc_data.get("building_elements", [])
        spatial_structure = parsed_ifc_data.get("spatial_structure", {})
        properties = parsed_ifc_data.get("materials_and_properties", []) # This includes materials
        # Note: materials_and_properties might need further separation based on IFCParserService's output.
        # For now, assuming 'properties' contains both.

        # 2. Analyze bridge components (classification)
        # The classify_bridge_elements method returns a dict with categorized elements.
        classified_elements = self.bim_analyzer.classify_bridge_elements(building_elements)

        # 3. Extract design parameters
        # The extract_design_parameters method takes elements and properties.
        design_parameters = self.bim_analyzer.extract_design_parameters(building_elements, properties)

        # Other analyses from BridgeBIMAnalyzer could be called here if needed for graph construction:
        # structural_relationships = self.bim_analyzer.analyze_structural_relationships(building_elements, spatial_structure)
        # material_usage = self.bim_analyzer.analyze_material_usage(properties, building_elements) # Assuming 'properties' contains materials
        # construction_sequence = self.bim_analyzer.extract_construction_sequence(building_elements)

        # 4. Construct knowledge nodes and relationships
        nodes = []
        relationships = []

        # Create nodes from spatial hierarchy
        spatial_nodes = self.create_spatial_hierarchy_nodes(spatial_structure)
        nodes.extend(spatial_nodes)

        # Create nodes from element properties (using classified elements and raw properties)
        # This might need refinement based on how properties are structured.
        # For now, let's assume building_elements contains enough data for nodes.
        element_prop_nodes = self.create_element_property_nodes(building_elements, properties)
        nodes.extend(element_prop_nodes)

        # Create relationships from design constraints/parameters
        design_rels = self.create_design_constraint_relationships(design_parameters)
        relationships.extend(design_rels)

        # TODO: Add relationships between spatial nodes, element nodes, and property nodes.
        # TODO: Add relationships from structural_relationships, material_usage, construction_sequence.

        # Placeholder for the final knowledge graph structure
        knowledge_graph = {
            "nodes": nodes,
            "relationships": relationships,
            "metadata": parsed_ifc_data.get("metadata"),
            "classified_elements_summary": {cat: len(items) for cat, items_dict in classified_elements.items() if isinstance(items_dict, dict) for sub_cat, items in items_dict.items()},
            "design_parameters_summary": design_parameters
        }

        return knowledge_graph

    def create_spatial_hierarchy_nodes(self, spatial_structure: Dict) -> List[Dict]:
        """
        Creates knowledge graph nodes for the spatial hierarchy (Project, Site, Building, Storey, Space).
        `spatial_structure` is the dict from IFCParserService.extract_spatial_structure.
        """
        nodes = []
        # Example node structure: {"id": "unique_id", "label": "NodeType", "properties": {}}

        if spatial_structure.get("project"):
            project_data = spatial_structure["project"]
            nodes.append({
                "id": project_data.get("id", "project_default_id"),
                "label": "Project",
                "properties": {"name": project_data.get("name")}
            })

        # Add nodes for sites, buildings, storeys, spaces similarly.
        # This is a simplified version. Relationships between these nodes also need to be created.
        # For example, a "CONTAINS" relationship from Project to Site, Site to Building, etc.

        return nodes

    def create_element_property_nodes(self, elements: List[Dict], properties: List[Dict]) -> List[Dict]:
        """
        Creates knowledge graph nodes for building elements and their properties.
        `elements` is the list of raw building elements from IFCParserService.
        `properties` is the list of materials and properties from IFCParserService.
        """
        nodes = []
        # Example: Create a node for each element
        for element in elements:
            nodes.append({
                "id": element.get("id", f"element_{element.get('name', 'unnamed')}"),
                "label": element.get("type", "BuildingElement"), # e.g., "IfcBeam"
                "properties": {
                    "name": element.get("name"),
                    "tag": element.get("tag")
                    # Add more properties from the element dictionary
                }
            })

        # TODO: Process the `properties` list (which contains IfcPropertySet, IfcMaterial etc.)
        # and create distinct property nodes or attach them to element nodes.
        # This part needs careful design based on the desired graph schema.
        # For example, a material could be its own node, linked to elements.
        # A property set could also be a node, or its properties flattened into the element node.

        return nodes

    def create_design_constraint_relationships(self, parameters: Dict) -> List[Dict]:
        """
        Creates knowledge graph relationships representing design constraints or parameters.
        `parameters` is the dict from BridgeBIMAnalyzer.extract_design_parameters.
        """
        relationships = []
        # Example relationship: {"from_node_id": "X", "to_node_id": "Y", "type": "HAS_PARAMETER", "properties": {}}
        # Or, design parameters might be properties of a "Bridge" node or "Project" node.

        # This is highly dependent on the graph schema.
        # For now, this is a placeholder. One might create "Parameter" nodes and link them,
        # or add these parameters to a central "Bridge" or "Project" node.

        # Example: if there's a "Project" node, add these as properties or related nodes.
        # Let's assume we have a project_node_id (e.g., from create_spatial_hierarchy_nodes)
        # project_node_id = "project_default_id" # Placeholder
        # for key, value in parameters.items():
        #     if value is not None:
        #         # This could be adding properties to an existing node, or creating new relationship
        #         # For simplicity, let's imagine creating relationships to a conceptual "DesignParameter" node type
        #         param_node_id = f"param_{key}"
        #         # nodes.append({"id": param_node_id, "label": "DesignParameter", "properties": {"name": key, "value": value}})
        #         # relationships.append({
        #         #     "from_node_id": project_node_id,
        #         #     "to_node_id": param_node_id,
        #         #     "type": "HAS_DESIGN_PARAMETER"
        #         # })
        # This part needs more specific graph schema decisions.
        return relationships

if __name__ == '__main__':
    # Placeholder for testing
    # builder = BIMKnowledgeBuilder()
    # sample_ifc_file = "path/to/your/sample.ifc" # Needs a real IFC file
    # if os.path.exists(sample_ifc_file):
    #     kg_data = builder.build_knowledge_from_bim(sample_ifc_file)
    #     import json
    #     print(json.dumps(kg_data, indent=2))
    # else:
    #     print(f"Sample IFC file not found at: {sample_ifc_file}")
    pass
