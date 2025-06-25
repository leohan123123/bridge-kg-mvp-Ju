from typing import Dict, List, Any
# Ensure correct relative imports if these services are in the same directory or a structured package
# For a flat structure under backend/app/services/ :
from app.services.dxf_parser import DXFParserService
from app.services.bridge_drawing_analyzer import BridgeDrawingAnalyzer
import uuid # For generating unique IDs for entities if needed

class DrawingKnowledgeExtractor:
    def __init__(self):
        self.dxf_parser = DXFParserService()
        self.drawing_analyzer = BridgeDrawingAnalyzer()

    def extract_knowledge_from_drawing(self, file_path: str) -> Dict[str, Any]:
        """
        Orchestrates the extraction of structured knowledge from a DXF drawing.
        1. Parses the DXF file.
        2. Analyzes professional content (bridge-specific).
        3. Structures entities and relationships for KG.
        Returns a dictionary representing the extracted knowledge.
        """
        # 1. Parse DXF file
        parsed_dxf_data = self.dxf_parser.parse_dxf_file(file_path)

        if parsed_dxf_data.get("error"):
            return {"error": parsed_dxf_data["error"], "nodes": [], "edges": []}

        # 2. Analyze professional content
        drawing_type = self.drawing_analyzer.identify_drawing_type(parsed_dxf_data)
        # Components are extracted based on all entities, including text and geometry
        bridge_components_analysis = self.drawing_analyzer.extract_bridge_components(parsed_dxf_data)
        dimensions_specs_analysis = self.drawing_analyzer.extract_dimensions_and_specs(parsed_dxf_data)
        material_specs_analysis = self.drawing_analyzer.extract_material_specifications(parsed_dxf_data)
        # Structural relationships analysis is currently basic
        structural_relationships_analysis = self.drawing_analyzer.analyze_structural_relationships(parsed_dxf_data)

        # 3. & 4. Create knowledge graph elements (nodes and edges)
        # This is a conceptual representation. The actual KG structure might vary.
        nodes = []
        edges = []

        # Document Node
        doc_id = f"document_{uuid.uuid4()}"
        nodes.append({
            "id": doc_id,
            "type": "DrawingDocument",
            "label": parsed_dxf_data.get("metadata", {}).get("filename", "Unnamed Drawing"),
            "dxf_version": parsed_dxf_data.get("metadata", {}).get("dxf_version"),
            "drawing_type_identified": drawing_type,
            "file_path": file_path
        })

        # Layer Nodes
        for layer in parsed_dxf_data.get("layers", []):
            layer_id = f"layer_{layer['name'].replace(' ', '_')}_{uuid.uuid4()}"
            nodes.append({
                "id": layer_id,
                "type": "Layer",
                "label": layer['name'],
                **layer # Add all other layer properties
            })
            edges.append({"source": doc_id, "target": layer_id, "label": "has_layer"})

        # Geometric Entity Nodes (simplified)
        # For a full KG, each entity could be a node. For summarization, we might group them.
        # Here, we call create_geometric_entities to get structured nodes.
        geometric_nodes, geometric_edges = self.create_geometric_entities(parsed_dxf_data.get("entities", []), doc_id)
        nodes.extend(geometric_nodes)
        edges.extend(geometric_edges)

        text_annotation_nodes, text_annotation_edges = self._create_text_annotation_nodes(parsed_dxf_data.get("text_annotations",[]), doc_id)
        nodes.extend(text_annotation_nodes)
        edges.extend(text_annotation_edges)


        # Bridge Component Nodes (based on analysis)
        comp_analysis_id = f"analysis_components_{uuid.uuid4()}"
        nodes.append({
            "id": comp_analysis_id,
            "type": "BridgeComponentAnalysis",
            "label": "Bridge Component Analysis Summary"
        })
        edges.append({"source": doc_id, "target": comp_analysis_id, "label": "has_component_analysis"})

        for comp_type, comp_list in bridge_components_analysis.items():
            if comp_list:
                comp_type_node_id = f"component_type_{comp_type}_{uuid.uuid4()}"
                nodes.append({
                    "id": comp_type_node_id,
                    "type": "BridgeComponentType",
                    "label": comp_type.capitalize(),
                    "count": len(comp_list)
                })
                edges.append({"source": comp_analysis_id, "target": comp_type_node_id, "label": "identifies_type"})
                # Optionally, create individual nodes for each identified component instance
                # For now, just linking the types.


        # Dimensions and Specs Node
        dims_specs_id = f"analysis_dims_specs_{uuid.uuid4()}"
        nodes.append({
            "id": dims_specs_id,
            "type": "DimensionsSpecificationsAnalysis",
            "label": "Dimensions and Specifications Summary",
            **dimensions_specs_analysis # Add all extracted data
        })
        edges.append({"source": doc_id, "target": dims_specs_id, "label": "has_dimensions_specs_analysis"})

        # Material Specs Node
        mats_specs_id = f"analysis_mats_specs_{uuid.uuid4()}"
        nodes.append({
            "id": mats_specs_id,
            "type": "MaterialSpecificationsAnalysis",
            "label": "Material Specifications Summary",
            **material_specs_analysis # Add all extracted data
        })
        edges.append({"source": doc_id, "target": mats_specs_id, "label": "has_material_specs_analysis"})

        # Add extracted materials to the dimensions_specs_analysis node as well for consolidation
        if dims_specs_id and any(nodes_item['id'] == dims_specs_id for nodes_item in nodes):
            next(item for item in nodes if item["id"] == dims_specs_id)['material_specs_summary'] = material_specs_analysis


        # Structural Relationships (if any meaningful ones are extracted)
        # rel_analysis_id = f"analysis_relationships_{uuid.uuid4()}"
        # nodes.append(...) for relationship summary
        # edges.append(...)
        # component_relationship_nodes, component_relationship_edges = self.create_component_relationships(structural_relationships_analysis, comp_analysis_id)
        # nodes.extend(component_relationship_nodes)
        # edges.extend(component_relationship_edges)


        return {
            "document_info": {
                "filename": parsed_dxf_data.get("metadata", {}).get("filename"),
                "dxf_version": parsed_dxf_data.get("metadata", {}).get("dxf_version"),
                "identified_drawing_type": drawing_type,
            },
            "analysis_summary": {
                "bridge_components": bridge_components_analysis,
                "dimensions_specifications": dimensions_specs_analysis,
                "material_specifications": material_specs_analysis,
                "structural_relationships": structural_relationships_analysis # Placeholder for now
            },
            "knowledge_graph": { # This is a conceptual KG structure
                "nodes": nodes,
                "edges": edges
            },
            "raw_parsed_data": parsed_dxf_data # Optionally include for debugging or further processing
        }

    def create_geometric_entities(self, geometric_data: List[Dict[str, Any]], parent_doc_id: str) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
        """
        Creates nodes for geometric entities and edges linking them to the parent document/drawing.
        This is a simplified representation; could be much more granular.
        """
        nodes = []
        edges = []
        # Summary node for all geometric entities
        # geom_summary_id = f"geometric_summary_{uuid.uuid4()}"
        # nodes.append({
        #     "id": geom_summary_id,
        #     "type": "GeometricEntitiesSummary",
        #     "label": f"Geometric Entities ({len(geometric_data)} items)",
        #     "count": len(geometric_data)
        # })
        # edges.append({"source": parent_doc_id, "target": geom_summary_id, "label": "has_geometric_summary"})

        # Alternatively, create nodes for each significant geometric entity or a sample
        for i, entity in enumerate(geometric_data):
            # Limit the number of individual geometric entity nodes for performance in large drawings
            # if i < 50 : # Example: Only create detailed nodes for the first 50 geometric entities
            entity_id = f"geom_entity_{entity.get('type', 'unknown').lower()}_{entity.get('handle', uuid.uuid4())}"
            nodes.append({
                "id": entity_id,
                "type": "GeometricEntity",
                "label": f"{entity.get('type', 'UnknownType')} (Handle: {entity.get('handle', 'N/A')})",
                "dxf_type": entity.get('type'),
                "layer": entity.get('layer'),
                "color": entity.get('color'),
                "details": entity.get('entity_specific', {})
            })
            edges.append({"source": parent_doc_id, "target": entity_id, "label": "contains_geometric_entity"})
            # Could also link to layer node if layer_id is available/passed
        return nodes, edges

    def _create_text_annotation_nodes(self, text_annotation_data: List[Dict[str, Any]], parent_doc_id: str) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
        nodes = []
        edges = []
        for i, entity in enumerate(text_annotation_data):
            entity_id = f"text_annot_{entity.get('type', 'unknown').lower()}_{entity.get('handle', uuid.uuid4())}"
            node_data = {
                "id": entity_id,
                "type": "TextAnnotationEntity",
                "label": f"{entity.get('type', 'UnknownType')} (Handle: {entity.get('handle', 'N/A')})",
                "dxf_type": entity.get('type'),
                "layer": entity.get('layer'),
                "details": entity.get('entity_specific', {})
            }
            if entity.get('type') in ["TEXT", "MTEXT"]:
                node_data["text_content"] = entity.get('entity_specific', {}).get('text_string', '')
            elif entity.get('type') == "DIMENSION":
                 node_data["text_content"] = entity.get('entity_specific', {}).get('text_content', '')
                 node_data["measurement"] = entity.get('entity_specific', {}).get('measurement')

            nodes.append(node_data)
            edges.append({"source": parent_doc_id, "target": entity_id, "label": "contains_text_annotation"})
        return nodes, edges


    def create_component_relationships(self, relationships_analysis: List[Dict[str, Any]], parent_analysis_id: str) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
        """
        Creates nodes and edges representing relationships between bridge components.
        This is highly dependent on the output of BridgeDrawingAnalyzer.analyze_structural_relationships.
        """
        nodes = []
        edges = []
        # For now, this is a placeholder as relationship analysis is basic.
        # If relationships_analysis provided structured data like:
        # [{"type": "supports", "from_component_id": "pier1", "to_component_id": "beam1"}]
        # Then we would create corresponding edges in the graph.

        for i, rel in enumerate(relationships_analysis):
            if rel.get("type") != "Conceptual": # Skip placeholder descriptions
                rel_id = f"comp_rel_{uuid.uuid4()}"
                nodes.append({
                    "id": rel_id,
                    "type": "ComponentRelationship",
                    "label": rel.get("type", "Unnamed Relationship"),
                    "description": rel.get("description"),
                    # "from_component": rel.get("from_component_id"), # These would need to be actual node IDs
                    # "to_component": rel.get("to_component_id")
                })
                # edges.append({"source": parent_analysis_id, "target": rel_id, "label": "found_relationship"})
                # edges.append({"source": rel.get("from_component_id"), "target": rel.get("to_component_id"), "label": rel.get("type")})
        return nodes, edges

# Example usage (for testing purposes)
if __name__ == '__main__':
    # This requires DXFParserService and BridgeDrawingAnalyzer to be available
    # and a sample DXF file.

    # Create a dummy DXF for basic testing
    import ezdxf
    import os
    import json

    temp_dxf_path = "temp_knowledge_extractor_test.dxf"
    try:
        test_doc = ezdxf.new('R2010')
        test_msp = test_doc.modelspace()
        test_doc.layers.new(name='BRIDGE_PIERS', dxfattribs={'color': 1})
        test_doc.layers.new(name='TEXT', dxfattribs={'color': 7})
        test_msp.add_line((0,0), (0,10), dxfattribs={'layer': 'BRIDGE_PIERS'})
        test_msp.add_text('Pier No.1', dxfattribs={'insert': (1,10), 'layer': 'TEXT'})
        test_msp.add_text('Concrete: C30', dxfattribs={'insert': (1,9), 'layer': 'TEXT'})
        test_msp.add_text('Overall Bridge Layout', dxfattribs={'insert': (10,20), 'layer': 'TEXT'})
        test_doc.saveas(temp_dxf_path)

        extractor = DrawingKnowledgeExtractor()
        knowledge_data = extractor.extract_knowledge_from_drawing(temp_dxf_path)

        print("\nExtracted Knowledge Data:")
        # Pretty print the JSON output
        print(json.dumps(knowledge_data, indent=2, ensure_ascii=False))

        # Basic check on output structure
        assert "document_info" in knowledge_data
        assert "analysis_summary" in knowledge_data
        assert "knowledge_graph" in knowledge_data
        assert "nodes" in knowledge_data["knowledge_graph"]
        assert "edges" in knowledge_data["knowledge_graph"]

        print(f"\nFound {len(knowledge_data['knowledge_graph']['nodes'])} nodes.")
        print(f"Found {len(knowledge_data['knowledge_graph']['edges'])} edges.")


    except ImportError as e:
        print(f"Import error, make sure DXFParserService and BridgeDrawingAnalyzer are in the python path: {e}")
    except FileNotFoundError:
        print(f"Test DXF file not found: {temp_dxf_path}. Cannot run example.")
    except Exception as e:
        print(f"An error occurred during example usage: {e}")
    finally:
        if os.path.exists(temp_dxf_path):
            os.remove(temp_dxf_path)

    print("\nDrawingKnowledgeExtractor implementation draft complete.")
