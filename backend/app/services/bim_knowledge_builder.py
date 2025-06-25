from typing import Dict, List, Any
# Ensure services are correctly importable. May need to adjust path if running standalone vs within FastAPI app
# For FastAPI, it would be:
# from app.services.ifc_parser_service import IFCParserService
# from app.services.bridge_bim_analyzer import BridgeBIMAnalyzer
# For now, assuming they are in the same directory or PYTHONPATH is set up for direct import if testing locally.
# Corrected imports for consistency with execution environment
from app.services.ifc_parser_service import IFCParserService
from app.services.bridge_bim_analyzer import BridgeBIMAnalyzer


class BIMKnowledgeBuilder:
    def __init__(self):
        self.ifc_parser = IFCParserService()
        self.bim_analyzer = BridgeBIMAnalyzer()

    def build_knowledge_from_bim(self, file_path: str) -> Dict[str, List[Dict]]:
        knowledge_graph = {
            "nodes": [],
            "relationships": []
        }

        # 1. Parse IFC file
        parsed_ifc_data = self.ifc_parser.parse_ifc_file(file_path)
        if parsed_ifc_data.get("error"):
            # Propagate error if IFC parsing failed
            return {"error": parsed_ifc_data["error"], "nodes": [], "relationships": []}

        project_metadata = parsed_ifc_data.get("metadata", {})
        spatial_structure_data = parsed_ifc_data.get("spatial_structure", {})
        elements_data = parsed_ifc_data.get("elements", [])
        materials_data = parsed_ifc_data.get("materials_properties", []) # Defined materials
        # geometry_summary = parsed_ifc_data.get("geometric_summary", []) # Not directly used for KG nodes yet

        # Create a project node
        project_node_id = project_metadata.get("name", "UnknownProject") # Use name as ID, or generate one
        if not project_metadata.get("name") and project_metadata.get("id"): # Fallback to project ID if available
             project_node_id = project_metadata.get("id", "UnknownProjectGlobalID")

        knowledge_graph["nodes"].append({
            "id": project_node_id,
            "type": "Project",
            "label": project_metadata.get("name", "Unnamed Project"),
            "properties": project_metadata
        })

        # 2. Create Spatial Hierarchy Nodes and Relationships
        spatial_nodes, spatial_relationships = self.create_spatial_hierarchy_nodes(
            spatial_structure_data.get("hierarchy", []), project_node_id
        )
        knowledge_graph["nodes"].extend(spatial_nodes)
        knowledge_graph["relationships"].extend(spatial_relationships)

        # 3. Analyze Bridge Elements (using BridgeBIMAnalyzer)
        classified_elements = self.bim_analyzer.classify_bridge_elements(elements_data)
        # `classified_elements` is a dict like {"superstructure": {"main_girders": [...]}}
        # We need to iterate through all elements regardless of classification for node creation first.

        # 4. Create Element Nodes and Property Relationships
        # Also link elements to their spatial context
        element_nodes, element_property_rels = self.create_element_property_nodes(
            elements_data, project_node_id, spatial_structure_data.get("hierarchy", [])
        )
        knowledge_graph["nodes"].extend(element_nodes)
        knowledge_graph["relationships"].extend(element_property_rels)

        # Add relationships based on classification
        for category, sub_categories in classified_elements.items():
            if category == "unclassified":
                for element_dict in sub_categories: # sub_categories is a list here
                    # Optionally add a "isA" relationship to a generic "UnclassifiedElement" type node
                    pass # Or just rely on the element's IFC type node
                continue

            for sub_category, elements_in_sub_category in sub_categories.items():
                for element_dict in elements_in_sub_category:
                    element_id = element_dict.get("id")
                    knowledge_graph["relationships"].append({
                        "source": element_id,
                        "target": f"BridgeComponentCategory:{category.replace('_',' ').title()}", # e.g. BridgeComponentCategory:Superstructure
                        "type": "isCategorizedAs",
                        "properties": {"sub_category": sub_category.replace('_',' ').title()}
                    })
                    # Create category nodes if they don't exist (simplified)
                    cat_node_id = f"BridgeComponentCategory:{category.replace('_',' ').title()}"
                    if not any(n["id"] == cat_node_id for n in knowledge_graph["nodes"]):
                        knowledge_graph["nodes"].append({"id": cat_node_id, "type": "BridgeComponentCategory", "label": category.replace('_',' ').title()})


        # 5. Extract Design Parameters (using BridgeBIMAnalyzer)
        # Project properties might be part of `project_metadata` or need specific handling
        project_props_for_analyzer = project_metadata.get("properties_extracted_separately", []) # Assuming a structure
        design_parameters = self.bim_analyzer.extract_design_parameters(elements_data, project_props_for_analyzer)

        # Create Design Parameter Nodes/Relationships
        # This could mean attaching parameters to existing element/project nodes
        # or creating separate parameter nodes and linking them.
        # For now, let's attach them as properties or create simple relationship for overall params.
        if design_parameters.get("overall_span"):
             knowledge_graph["relationships"].append({
                "source": project_node_id,
                "target": "OverallSpanParameterNode", # Conceptual node
                "type": "hasDesignParameter",
                "properties": {"name": "Overall Span", "value": design_parameters["overall_span"]}
            })
            # Add the parameter node if it doesn't exist (or just store as property of project)
            # For simplicity, many parameters can be properties of the project/element nodes directly.
            # Updating project node with these params:
            for node in knowledge_graph["nodes"]:
                if node["id"] == project_node_id:
                    node["properties"]["design_parameters"] = design_parameters # Attach all for now
                    break


        # 6. Analyze Material Usage (using BridgeBIMAnalyzer)
        material_usage_analysis = self.bim_analyzer.analyze_material_usage(materials_data, elements_data)
        # Add material nodes and link elements to them
        for mat_name, usage_details in material_usage_analysis.get("material_distribution", {}).items():
            mat_node_id = f"Material:{mat_name}"
            if not any(n["id"] == mat_node_id for n in knowledge_graph["nodes"]):
                # Try to find more details about this material from the materials_data list
                mat_props = next((m for m in materials_data if m.get("name") == mat_name), {"description": "N/A"})
                knowledge_graph["nodes"].append({
                    "id": mat_node_id,
                    "type": "Material",
                    "label": mat_name,
                    "properties": {"description": mat_props.get("description"), "category": mat_props.get("category")}
                })

            # Link elements that use this material
            for element_desc in usage_details: # e.g. "IfcBeam - Main Girder 1 (guid1)"
                # Need to get element_id from this description or have BridgeBIMAnalyzer return IDs
                # Assuming elements_data has the necessary IDs.
                # This part requires BridgeBIMAnalyzer.analyze_material_usage to provide element IDs.
                # Let's assume `elements_data` allows lookup by description or `material_usage_analysis` gives IDs.
                # For now, we'll iterate `elements_data` to find matches if `element.get("material")` is the mat_name
                for el_node in element_nodes: # Iterate over already created element nodes
                    el_data = next((e for e in elements_data if e["id"] == el_node["id"]), None)
                    if el_data and el_data.get("material"):
                        current_el_mats = []
                        if isinstance(el_data["material"], list):
                            current_el_mats.extend(el_data["material"])
                        elif isinstance(el_data["material"], str):
                            current_el_mats.append(el_data["material"])

                        if mat_name in current_el_mats:
                             knowledge_graph["relationships"].append({
                                "source": el_node["id"],
                                "target": mat_node_id,
                                "type": "hasMaterial",
                                "properties": {}
                            })


        # 7. Extract Construction Sequence (using BridgeBIMAnalyzer)
        construction_sequence = self.bim_analyzer.extract_construction_sequence(elements_data)
        if construction_sequence and not (len(construction_sequence) == 1 and "No explicit construction" in construction_sequence[0].get("message","")):
            seq_prop = {"construction_sequence": construction_sequence}
            # Could link this to project or create specific task nodes. For now, add to project properties.
            for node in knowledge_graph["nodes"]:
                if node["id"] == project_node_id:
                    if "properties" not in node:
                        node["properties"] = {}
                    node["properties"].update(seq_prop)
                    break

        # 8. (Optional) Design Constraint Relationships - Placeholder for now
        # design_constraints = self.create_design_constraint_relationships(design_parameters)
        # knowledge_graph["relationships"].extend(design_constraints)


        # Remove duplicate nodes and relationships (simple check by ID for nodes, by source/target/type for rels)
        final_nodes = {node['id']: node for node in knowledge_graph['nodes']}.values()

        seen_rels = set()
        final_relationships = []
        for rel in knowledge_graph['relationships']:
            rel_signature = (rel['source'], rel['target'], rel['type'])
            if rel_signature not in seen_rels:
                final_relationships.append(rel)
                seen_rels.add(rel_signature)

        return {"nodes": list(final_nodes), "relationships": list(final_relationships)}


    def _find_spatial_parent_id(self, element_id: str, hierarchy: List[Dict]):
        # Helper to find the direct parent ID in the spatial hierarchy for an element
        # This needs a robust way to know how elements are linked to spatial zones in parsed_ifc_data
        # IFCParserService.extract_building_elements should ideally include parent spatial zone ID.
        # For now, this is a simplified placeholder.
        # A common way is via IfcRelContainedInSpatialStructure.
        # If element data has 'contained_in_structure_guid', we can use that.
        # This function might not be needed if create_element_property_nodes handles it.
        return None

    def create_spatial_hierarchy_nodes(self, hierarchy_data: List[Dict], project_node_id: str) -> (List[Dict], List[Dict]):
        nodes = []
        relationships = []

        def process_level(items: List[Dict], parent_id: str):
            for item in items:
                node_id = item.get("id")
                if not node_id: # Should always have an ID from parser
                    node_id = f"{item.get('level', 'SpatialZone')}:{item.get('name', 'UnnamedZone')}" # Fallback ID

                # Avoid re-creating the project node if it's the root of hierarchy_data
                if node_id == project_node_id and item.get("level") == "Project":
                     # The project node is already created, just ensure parent_id logic works for its children
                     pass # Project node already exists
                else:
                    nodes.append({
                        "id": node_id,
                        "type": item.get("level", item.get("type", "SpatialZone")), # Use level (Project, Site) or IFC type
                        "label": item.get("name", item.get("id")),
                        "properties": {k: v for k, v in item.items() if k not in ["id", "name", "level", "children", "type"]}
                    })

                if parent_id and node_id != parent_id : # Don't link project to itself if it was passed as parent_id
                    relationships.append({
                        "source": parent_id, # Parent (e.g. Project ID)
                        "target": node_id,   # Child (e.g. Site ID)
                        "type": "decomposes" if item.get("level") in ["Site", "Building", "Storey", "Space"] else "contains", # Or "aggregates"
                        "properties": {}
                    })

                if item.get("children"):
                    process_level(item["children"], node_id) # Current item becomes parent for its children

        process_level(hierarchy_data, project_node_id) # Start with project as ultimate parent
        return nodes, relationships

    def create_element_property_nodes(self, elements: List[Dict], project_node_id: str, spatial_hierarchy: List[Dict]) -> (List[Dict], List[Dict]):
        nodes = []
        relationships = []

        # Create a map of spatial zone GUIDs to their KG node IDs for quick lookup
        spatial_id_map = {}
        def build_spatial_map(items_list):
            for item in items_list:
                spatial_id_map[item.get("id")] = item.get("id") # Assuming KG node ID is same as IFC GUID for spatial zones
                if item.get("children"):
                    build_spatial_map(item.get("children"))
        build_spatial_map(spatial_hierarchy)


        for element in elements:
            elem_id = element.get("id")
            elem_type_full = element.get("type", "IfcBuildingElement") # Full IFC Type
            elem_type_simple = elem_type_full.replace("Ifc", "") # Simpler type for KG node type

            nodes.append({
                "id": elem_id,
                "type": elem_type_simple, # e.g., "Beam", "Column"
                "label": element.get("name", elem_id),
                "properties": {
                    "ifc_type": elem_type_full,
                    "tag": element.get("tag"),
                    "description": element.get("description"),
                    # Raw properties can be stored here or broken down
                    "ifc_properties": element.get("properties", [])
                }
            })

            # Link element to project (e.g. "belongsToProject") - can be too many, consider linking to spatial zone
            # relationships.append({
            #     "source": elem_id, "target": project_node_id, "type": "partOfProject", "properties": {}
            # })

            # Link element to its containing spatial structure
            # This assumes `IFCParserService.extract_building_elements` adds a field like `contained_in_spatial_id`
            # If not, this part needs adjustment or to happen in IFCParserService.
            # For now, this is a placeholder logic.
            # A more robust way is for IFCParser to resolve IfcRelContainedInSpatialStructure
            # and add `RelatingStructureGlobalId` to the element dict.

            # Let's assume `element` dict might have a `parent_spatial_structure_id` key from a more advanced parser.
            # If not, this link might be harder to establish here without passing the full ifc_file.
            # The `_find_spatial_parent_id` was a placeholder for this.
            # For now, we'll skip direct spatial parent linking here if not readily available on element.
            # The spatial hierarchy itself shows zones, and elements are listed; visualizers often handle this.


            # Create relationships for PSet properties (can be verbose)
            # Option 1: Store Psets directly as a JSON property (done above in "ifc_properties")
            # Option 2: Create separate nodes for Psets and properties (more granular, more complex graph)
            # For now, keeping them as JSON properties on the element node is simpler.
            # If specific properties need to be queryable as distinct nodes/rels:
            # for pset in element.get("properties", []):
            #     pset_node_id = f"{elem_id}_Pset_{pset.get('name')}"
            #     nodes.append({"id": pset_node_id, "type": "PropertySet", "label": pset.get('name')})
            #     relationships.append({"source": elem_id, "target": pset_node_id, "type": "hasPropertySet"})
            #     for key, value in pset.get("values", {}).items():
            #         prop_node_id = f"{pset_node_id}_Prop_{key}"
            #         nodes.append({"id": prop_node_id, "type": "Property", "label": key, "properties": {"value": value}})
            #         relationships.append({"source": pset_node_id, "target": prop_node_id, "type": "hasProperty"})
            pass # Properties are embedded for now

        return nodes, relationships

    def create_design_constraint_relationships(self, parameters: Dict) -> List[Dict]:
        # This is a placeholder for creating relationships based on design parameters.
        # Example: If a parameter is "LoadBearingCapacity > 500kN", this could be a constraint node.
        # For now, parameters are mostly added as properties to relevant nodes.
        return []


if __name__ == '__main__':
    # This test requires:
    # 1. ifc_parser_service.py and bridge_bim_analyzer.py in the same directory or PYTHONPATH
    # 2. A sample IFC file (e.g., "sample.ifc")
    # 3. ifcopenshell installed

    # Create a dummy IFC file for testing (very basic)
    # This is complex to do correctly without involving ifcopenshell's file creation API deeply.
    # For robust testing, a real, simple IFC file is better.

    print("BIMKnowledgeBuilder defined.")
    print("To test, create an instance and call build_knowledge_from_bim('path/to/sample.ifc')")

    # builder = BIMKnowledgeBuilder()
    # try:
    #     # Create a minimal dummy IFC file for testing ifcopenshell integration
    #     # Note: Programmatic IFC creation is non-trivial. This is a placeholder.
    #     # A real test would use a pre-existing valid IFC file.
    #     # For now, we'll assume the methods will be called by other parts of the application
    #     # which provide a valid file_path.
    #     print("Note: Full test of build_knowledge_from_bim requires a valid IFC file.")
    #     print("Consider testing with a small, standard IFC model.")

    #     # Example (conceptual - would need a file):
    #     # kg_data = builder.build_knowledge_from_bim("test_file.ifc") # replace with actual file
    #     # if "error" in kg_data:
    #     #    print(f"Error: {kg_data['error']}")
    #     # else:
    #     #    print("Knowledge Graph Nodes:", len(kg_data["nodes"]))
    #     #    print("Knowledge Graph Relationships:", len(kg_data["relationships"]))
    #     #    # print(json.dumps(kg_data, indent=2)) # for detailed output
    # except Exception as e:
    #     print(f"An error occurred during __main__ test: {e}")
    #     import traceback
    #     traceback.print_exc()

    pass
