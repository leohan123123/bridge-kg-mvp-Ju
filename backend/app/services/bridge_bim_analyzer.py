from typing import Dict, List, Any

# A placeholder for a more sophisticated BridgeEntityExtractor if needed in the future.
# For now, classification logic will be within BridgeBIMAnalyzer.
class BridgeEntityExtractor:
    def __init__(self):
        pass

    def get_element_type_and_properties(self, element: Dict) -> Dict:
        # This could be used to pre-process or enrich element data before classification
        return {"ifc_type": element.get("type"), "name": element.get("name"), "properties": element.get("properties", [])}


class BridgeBIMAnalyzer:
    def __init__(self):
        self.bridge_extractor = BridgeEntityExtractor() # Not strictly used yet, but as per plan

    def classify_bridge_elements(self, elements: List[Dict]) -> Dict[str, List[Dict]]:
        classified_elements = {
            "superstructure": {"main_girders": [], "cross_girders": [], "deck_slabs": [], "others": []},
            "substructure": {"piers": [], "abutments": [], "foundations": [], "piles": [], "others": []},
            "accessories": {"railings": [], "expansion_joints": [], "drainage": [], "bearings": [], "others": []},
            "unclassified": []
        }

        # Keywords and IFC types for classification (example, needs refinement)
        # This is highly dependent on how elements are named and typed in the IFC models.
        # More robust classification might involve checking specific properties or IfcObjecttype.

        superstructure_keywords = {
            "main_girders": ["main girder", "main beam", "box girder"],
            "cross_girders": ["cross girder", "cross beam", "diaphragm"],
            "deck_slabs": ["deck slab", "bridge deck", "slab"],
        }
        substructure_keywords = {
            "piers": ["pier", "column", "bent"],
            "abutments": ["abutment"],
            "foundations": ["foundation", "footing", "pile cap"],
            "piles": ["pile"]
        }
        accessories_keywords = {
            "railings": ["railing", "parapet", "handrail"],
            "expansion_joints": ["expansion joint", "joint"],
            "drainage": ["drain", "scupper", "pipe"],
            "bearings": ["bearing", "pot bearing", "elastomeric bearing"]
        }

        for element in elements:
            elem_type = element.get("type", "").lower()
            elem_name = (element.get("name") or "").lower()
            elem_tag = (element.get("tag") or "").lower()
            description = (element.get("description") or "").lower()
            text_to_search = f"{elem_name} {elem_tag} {description}"

            classified = False

            # Superstructure
            if any(k_word in text_to_search for k_word in superstructure_keywords["main_girders"]) or \
               (elem_type == "ifcbeam" and ("main" in text_to_search or "girder" in text_to_search)):
                classified_elements["superstructure"]["main_girders"].append(element)
                classified = True
            elif any(k_word in text_to_search for k_word in superstructure_keywords["cross_girders"]) or \
                 (elem_type == "ifcbeam" and ("cross" in text_to_search or "diaphragm" in text_to_search)):
                classified_elements["superstructure"]["cross_girders"].append(element)
                classified = True
            elif any(k_word in text_to_search for k_word in superstructure_keywords["deck_slabs"]) or \
                 elem_type == "ifcslab": # Often IfcSlab is used for deck
                classified_elements["superstructure"]["deck_slabs"].append(element)
                classified = True

            # Substructure (ensure not already classified)
            if not classified:
                if any(k_word in text_to_search for k_word in substructure_keywords["piers"]) or \
                   elem_type == "ifccolumn":
                    classified_elements["substructure"]["piers"].append(element)
                    classified = True
                elif any(k_word in text_to_search for k_word in substructure_keywords["abutments"]) or \
                     (elem_type == "ifcwall" and "abutment" in text_to_search): # Abutments often modeled as IfcWall
                    classified_elements["substructure"]["abutments"].append(element)
                    classified = True
                elif any(k_word in text_to_search for k_word in substructure_keywords["foundations"]) or \
                     elem_type == "ifcfooting" or elem_type == "ifcfoundation":
                    classified_elements["substructure"]["foundations"].append(element)
                    classified = True
                elif any(k_word in text_to_search for k_word in substructure_keywords["piles"]) or \
                     elem_type == "ifcpile":
                    classified_elements["substructure"]["piles"].append(element)
                    classified = True

            # Accessories (ensure not already classified)
            if not classified:
                if any(k_word in text_to_search for k_word in accessories_keywords["railings"]) or \
                   elem_type == "ifcrailing":
                    classified_elements["accessories"]["railings"].append(element)
                    classified = True
                elif any(k_word in text_to_search for k_word in accessories_keywords["expansion_joints"]) or \
                     (elem_type == "ifcbuildingelementproxy" and "joint" in text_to_search): # Often proxies
                    classified_elements["accessories"]["expansion_joints"].append(element)
                    classified = True
                elif any(k_word in text_to_search for k_word in accessories_keywords["drainage"]):
                    classified_elements["accessories"]["drainage"].append(element)
                    classified = True
                elif any(k_word in text_to_search for k_word in accessories_keywords["bearings"]) or \
                     elem_type == "ifcbearing":
                    classified_elements["accessories"]["bearings"].append(element)
                    classified = True

            # Default classification based on IFC type if not caught by keywords
            if not classified:
                if elem_type in ["ifcbeam", "ifcplate", "ifcmember"]: # General superstructure elements
                    classified_elements["superstructure"]["others"].append(element)
                    classified = True
                elif elem_type in ["ifcwall", "ifcfooting", "ifcfoundation"] : # General substructure
                    classified_elements["substructure"]["others"].append(element)
                    classified = True
                elif elem_type in ["ifcbuildingelementproxy", "ifcdiscreteaccessory", "ifcfastener"]: # General accessories
                     classified_elements["accessories"]["others"].append(element)
                     classified = True


            if not classified:
                classified_elements["unclassified"].append(element)

        return classified_elements

    def analyze_structural_relationships(self, elements: List[Dict], spatial_structure: Dict) -> List[Dict]:
        # This is a complex task. For now, we'll focus on identifying
        # containment relationships based on the spatial structure provided by IFCParserService.
        # True structural connectivity (e.g. beam supported by column) often requires
        # analyzing IfcRelConnects subtypes and geometry, which is advanced.

        relationships = []

        # Example: Element A is spatially contained in Storey B
        # The spatial_structure from IFCParserService already contains this hierarchy.
        # We can re-format it or use it directly.
        # For this MVP, we might just return a statement that relationships
        # are implicitly in the spatial_structure and element data.

        # A more direct approach: iterate elements and see which spatial zone they belong to.
        # This info is usually part of IfcRelContainedInSpatialStructure,
        # which IFCParserService's spatial_structure should reflect.

        # Placeholder for more advanced relationship analysis:
        # - Support relationships (e.g., IfcRelConnectsStructuralMember)
        # - Connection relationships (e.g., IfcRelConnectsElements)
        # - Adjacency (geometric analysis)

        # For now, we'll assume the `spatial_structure` dict itself is a representation of one type of relationship.
        # And properties within elements might hint at others (e.g. "ConnectedTo" custom property).

        # Example: find elements that are part of a specific IfcBuildingStorey or IfcSpace
        # This requires cross-referencing element IDs with the spatial hierarchy.
        # The current `extract_spatial_structure` builds the hierarchy of spatial zones.
        # To link elements to these zones, we'd typically look at `element.ContainedInStructure`
        # during the initial parsing or pass the raw `ifc_file` object here (less ideal).

        # Let's assume `elements` list from `IFCParserService.extract_building_elements`
        # might eventually include a `contained_in_spatial_structure_id` field.
        # For now, this function will be a placeholder.

        relationships.append({
            "type": "SpatialContainment",
            "description": "Relationships based on IfcRelContainedInSpatialStructure are implicitly part of the spatial_structure output and element properties.",
            "details": "See 'spatial_structure' from IFCParserService and properties of individual elements."
        })

        return relationships


    def extract_design_parameters(self, elements: List[Dict], properties: List[Dict] = None) -> Dict:
        # 'properties' argument might be redundant if 'elements' already contain their properties.
        # This method will search for common bridge design parameters within element properties.
        # These are often stored in IfcPropertySet with specific names.

        design_params = {
            "overall_span": None, # Bridge level
            "girder_heights": [], # Per girder
            "deck_width": None, # Bridge or deck slab level
            "load_ratings": [], # Could be project or element level
            "clearances": {"vertical": None, "horizontal": None} # Bridge or specific locations
        }

        # Helper to search for a property value
        def find_prop_value(element_props: List[Dict], pset_name_keywords: List[str], prop_name_keywords: List[str]):
            for pset in element_props:
                pset_name_lower = pset.get("name", "").lower()
                if any(keyword in pset_name_lower for keyword in pset_name_keywords):
                    for prop_key, prop_value in pset.get("values", {}).items():
                        prop_key_lower = prop_key.lower()
                        if any(keyword in prop_key_lower for keyword in prop_name_keywords):
                            return prop_value
            return None

        # Search for parameters (this is highly heuristic and depends on model conventions)
        for element in elements:
            props = element.get("properties", [])
            elem_type = element.get("type")
            elem_name = (element.get("name") or "").lower()

            # Girder height (assuming 'IfcBeam' are girders)
            if elem_type == "IfcBeam" and ("girder" in elem_name or "beam" in elem_name):
                # Try common property names for height/depth
                height = find_prop_value(props, ["dimensions", "geometry", "parameters"], ["height", "depth", "h", "d"])
                if height:
                    design_params["girder_heights"].append({"element_id": element.get("id"), "height": height})

            # Deck width (from IfcSlab identified as deck)
            if elem_type == "IfcSlab" and "deck" in elem_name:
                width = find_prop_value(props, ["dimensions", "geometry", "parameters"], ["width", "w"])
                if width and design_params["deck_width"] is None: # Take first found for now
                    design_params["deck_width"] = width

            # Load ratings (could be on IfcProject, IfcBridge, or specific elements)
            # This is very custom. Example search:
            load_rating = find_prop_value(props, ["general", "design", "loading", "parameters"], ["load rating", "live load", "design load"])
            if load_rating:
                design_params["load_ratings"].append({"element_id": element.get("id"), "rating": load_rating})

        # Overall span and clearances are often project-level or require geometric analysis.
        # For now, these might remain None or be sought in IfcProject properties if available.
        # If `properties` argument was meant for project-level properties:
        if properties: # Assuming this is a list of project-level property sets
            overall_span = find_prop_value(properties, ["general", "design", "dimensions"], ["overall span", "total length", "bridge length"])
            if overall_span: design_params["overall_span"] = overall_span

            v_clearance = find_prop_value(properties, ["general", "design", "clearance"], ["vertical clearance", "headroom"])
            if v_clearance: design_params["clearances"]["vertical"] = v_clearance

            h_clearance = find_prop_value(properties, ["general", "design", "clearance"], ["horizontal clearance", "navigation width"])
            if h_clearance: design_params["clearances"]["horizontal"] = h_clearance

        # Remove empty lists from parameters for cleaner output
        design_params["girder_heights"] = [h for h in design_params["girder_heights"] if h["height"] is not None]
        design_params["load_ratings"] = [lr for lr in design_params["load_ratings"] if lr["rating"] is not None]
        if not design_params["girder_heights"]: del design_params["girder_heights"]
        if not design_params["load_ratings"]: del design_params["load_ratings"]

        return design_params

    def analyze_material_usage(self, materials_summary: List[Dict], elements: List[Dict]) -> Dict:
        # `materials_summary` is from `IFCParserService.extract_materials_and_properties` (list of defined materials)
        # `elements` is from `IFCParserService.extract_building_elements` (elements with their assigned materials)

        material_usage = {
            "by_element_type": {}, # e.g., {"IfcBeam": {"Concrete C30/37": 120, "Steel S355": 15}} (quantities are tricky)
            "material_quantities": {}, # e.g., {"Concrete C30/37": 500, "Steel S355": 50} (total quantities)
            "material_distribution": {} # e.g., {"Concrete C30/37": ["Main Girder 1", "Deck Slab"]}
        }

        # For now, we will focus on listing materials used by elements and their distribution.
        # Actual quantities (volume, mass) require IfcElementQuantity and are complex.

        temp_material_distribution = {}

        for element in elements:
            elem_id = element.get("id")
            elem_name = element.get("name", "Unnamed Element")
            elem_ifc_type = element.get("type", "UnknownType")

            mat_info = element.get("material")
            if mat_info:
                current_materials = []
                if isinstance(mat_info, list):
                    current_materials.extend(mat_info)
                elif isinstance(mat_info, str):
                    current_materials.append(mat_info)

                for mat_name in current_materials:
                    if mat_name not in temp_material_distribution:
                        temp_material_distribution[mat_name] = []
                    temp_material_distribution[mat_name].append(f"{elem_ifc_type} - {elem_name} ({elem_id})")

                    # Aggregate by element type (simple count of elements using the material)
                    if elem_ifc_type not in material_usage["by_element_type"]:
                        material_usage["by_element_type"][elem_ifc_type] = {}
                    if mat_name not in material_usage["by_element_type"][elem_ifc_type]:
                        material_usage["by_element_type"][elem_ifc_type][mat_name] = 0
                    material_usage["by_element_type"][elem_ifc_type][mat_name] += 1

        material_usage["material_distribution"] = temp_material_distribution

        # Summarize total counts for 'material_quantities' (as element counts per material for now)
        for mat_name, elements_using_it in temp_material_distribution.items():
            material_usage["material_quantities"][mat_name] = len(elements_using_it)

        return material_usage

    def extract_construction_sequence(self, elements: List[Dict]) -> List[Dict]:
        # Construction sequence information is typically stored in IfcTask, IfcWorkSchedule,
        # or via specific property sets on elements indicating phases or sequences.
        # This is an advanced topic and depends heavily on how the IFC model is authored.

        # For this MVP, we'll do a simplified check for common properties related to sequencing.
        sequence_info = []

        for element in elements:
            props = element.get("properties", [])
            construction_phase = find_prop_value(props, ["construction", "phasing", "sequence"],
                                                ["phase", "stage", "sequence_number", "construction_order"])
            if construction_phase:
                sequence_info.append({
                    "element_id": element.get("id"),
                    "element_name": element.get("name"),
                    "element_type": element.get("type"),
                    "phase_info": construction_phase
                })

        if not sequence_info:
            return [{"message": "No explicit construction sequence information found in element properties."}]

        # Sort by phase info if it's sortable (e.g., numeric)
        try:
            # Attempt to sort if phase_info is numeric or consistently prefixed (e.g., "Phase 1")
            # This is a naive sort, real sorting would need more robust parsing of phase_info
            sequence_info.sort(key=lambda x: str(x["phase_info"]))
        except TypeError:
            # Cannot sort if phase_info types are mixed or complex
            pass

        return sequence_info

# Helper function (already defined above, but good to have it standalone if used elsewhere)
def find_prop_value(element_props: List[Dict], pset_name_keywords: List[str], prop_name_keywords: List[str]):
    for pset in element_props:
        pset_name_lower = pset.get("name", "").lower()
        if any(keyword in pset_name_lower for keyword in pset_name_keywords):
            for prop_key, prop_value in pset.get("values", {}).items():
                prop_key_lower = prop_key.lower()
                if any(keyword in prop_key_lower for keyword in prop_name_keywords):
                    return prop_value
    return None

if __name__ == '__main__':
    # Example Usage (requires sample element data)
    analyzer = BridgeBIMAnalyzer()

    sample_elements = [
        {"id": "guid1", "type": "IfcBeam", "name": "Main Girder 1", "properties": [
            {"name": "Pset_BeamCommon", "values": {"Reference": "MB1", "LoadBearing": True}},
            {"name": "Dimensions", "values": {"Depth": 1.5, "Width": 0.5}}
        ], "material": "Concrete C40/50"},
        {"id": "guid2", "type": "IfcColumn", "name": "Pier Cap Column 1", "properties": [], "material": "Concrete C35/45"},
        {"id": "guid3", "type": "IfcSlab", "name": "Deck Section 1", "properties": [
             {"name": "Pset_SlabCommon", "values": {"AcousticRating": "Low"}},
             {"name": "Dimensions", "values": {"Width": 12.0, "Thickness": 0.25}}
        ], "material": "Concrete C30/37"},
        {"id": "guid4", "type": "IfcRailing", "name": "Safety Railing Type A", "properties": [], "material": "Steel S235"},
        {"id": "guid5", "type": "IfcBuildingElementProxy", "name": "Expansion Joint EJ-1", "properties": [
            {"name": "Construction", "values": {"Phase": "2"}}
        ]},
        {"id": "guid6", "type": "IfcBeam", "name": "Cross Beam D1", "properties": [
            {"name": "Dimensions", "values": {"Height": 0.8}} # Using "Height" here
        ], "material": "Concrete C40/50"},
         {"id": "guid7", "type": "IfcFooting", "name": "Foundation F1", "properties": [
            {"name": "Construction", "values": {"Phase": "1", "Sequence_Number": 10}}
        ], "material": "Concrete C25/30"},
    ]

    classified = analyzer.classify_bridge_elements(sample_elements)
    print("--- Classified Elements ---")
    import json
    print(json.dumps(classified, indent=2))

    # Assuming 'project_properties' would be parsed similarly to element properties by IFCParserService
    sample_project_properties = [
        {"name": "Pset_ProjectCommon", "values": {"ProjectName": "New Bridge X"}},
        {"name": "BridgeDesignParameters", "values": {"Overall Span": "120 m", "Design Load": "Eurocode Class I"}}
    ]
    design_params = analyzer.extract_design_parameters(sample_elements, sample_project_properties)
    print("\n--- Design Parameters ---")
    print(json.dumps(design_params, indent=2))

    # `sample_materials_summary` would come from IFCParserService.extract_materials_and_properties
    sample_materials_summary = [
        {"name": "Concrete C40/50", "description": "High strength concrete"},
        {"name": "Concrete C35/45", "description": "Standard concrete"},
        {"name": "Concrete C30/37", "description": "Standard concrete"},
        {"name": "Steel S235", "description": "Structural steel"},
        {"name": "Concrete C25/30", "description": "Foundation concrete"},
    ]
    material_usage = analyzer.analyze_material_usage(sample_materials_summary, sample_elements)
    print("\n--- Material Usage ---")
    print(json.dumps(material_usage, indent=2))

    construction_seq = analyzer.extract_construction_sequence(sample_elements)
    print("\n--- Construction Sequence ---")
    print(json.dumps(construction_seq, indent=2))

    # analyze_structural_relationships needs spatial_structure data
    # For now, it returns a placeholder.
    relationships = analyzer.analyze_structural_relationships(sample_elements, {})
    print("\n--- Structural Relationships ---")
    print(json.dumps(relationships, indent=2))

    print("\nBridgeBIMAnalyzer defined and basic tests run.")
