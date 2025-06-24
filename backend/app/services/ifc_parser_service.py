import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.pset
from typing import Dict, List

class IFCParserService:
    def __init__(self):
        # No specific initialization needed for ifcopenshell in the constructor
        pass

    def parse_ifc_file(self, file_path: str) -> Dict:
        try:
            ifc_file = ifcopenshell.open(file_path)
        except Exception as e:
            # Handle file opening errors, e.g., file not found or corrupt IFC
            return {"error": f"Failed to open IFC file: {str(e)}", "entities": [], "relationships": [], "properties": [], "metadata": {}}

        project_info = self.extract_project_info(ifc_file)
        spatial_structure = self.extract_spatial_structure(ifc_file)
        building_elements = self.extract_building_elements(ifc_file)
        materials_properties = self.extract_materials_and_properties(ifc_file)
        # Geometric representations can be extensive; decide if a summary or specific extraction is needed
        # For now, we'll return a placeholder or a count.
        geometric_representations_summary = self.extract_geometric_representations(ifc_file)


        return {
            "metadata": project_info,
            "spatial_structure": spatial_structure,
            "elements": building_elements, # Renamed from "entities" for clarity
            "materials_properties": materials_properties, # Renamed from "properties"
            "geometric_summary": geometric_representations_summary,
            # "relationships" can be derived from spatial structure and element connections
        }

    def extract_project_info(self, ifc_file) -> Dict:
        project_info = {}
        project = ifc_file.by_type("IfcProject")
        if project:
            p = project[0]
            project_info["name"] = p.Name or p.LongName
            project_info["description"] = p.Description

            # Units
            units = []
            for unit_assignment in ifc_file.by_type("IfcUnitAssignment"):
                for unit in unit_assignment.Units:
                    if unit.is_a("IfcSIUnit"):
                        units.append({
                            "type": unit.UnitType,
                            "prefix": unit.Prefix,
                            "name": unit.Name
                        })
            project_info["units"] = units

            # Coordinate System
            contexts = p.RepresentationContexts
            for context in contexts:
                if context.ContextType == 'Model':
                    project_info["coordinate_system_name"] = context.ContextIdentifier
                    if hasattr(context, 'CoordinateSpaceDimension'):
                         project_info["coordinate_space_dimension"] = context.CoordinateSpaceDimension
                    if hasattr(context, 'Precision'):
                        project_info["precision"] = context.Precision
                    if hasattr(context, 'WorldCoordinateSystem') and context.WorldCoordinateSystem:
                        wcs = context.WorldCoordinateSystem
                        project_info["world_coordinate_system_origin"] = wcs.Location.Coordinates if wcs.Location else None
                        # More WCS details can be added if needed
                    break # Assuming one main model context
        return project_info

    def _get_element_basic_info(self, element):
        return {
            "id": element.GlobalId,
            "type": element.is_a(),
            "name": element.Name,
            "tag": element.Tag if hasattr(element, 'Tag') else None,
            "description": element.Description if hasattr(element, 'Description') else None,
        }

    def extract_spatial_structure(self, ifc_file) -> Dict:
        spatial_structure_info = {"hierarchy": []}

        # Helper to recursively build hierarchy
        def build_hierarchy(element, level_name):
            item = self._get_element_basic_info(element)
            item["level"] = level_name
            item["children"] = []

            # Decomposes (IfcRelAggregates)
            if hasattr(element, 'IsDecomposedBy'):
                for rel in element.IsDecomposedBy:
                    if rel.is_a("IfcRelAggregates"):
                        for child_object in rel.RelatedObjects:
                            # Determine child level based on parent
                            child_level_name = "Unknown"
                            if child_object.is_a("IfcSite"): child_level_name = "Site"
                            elif child_object.is_a("IfcBuilding"): child_level_name = "Building"
                            elif child_object.is_a("IfcBuildingStorey"): child_level_name = "Storey"
                            elif child_object.is_a("IfcSpace"): child_level_name = "Space"
                            else: child_level_name = child_object.is_a() # Fallback to IFC type
                            item["children"].append(build_hierarchy(child_object, child_level_name))

            # Spatial containment (IfcRelContainedInSpatialStructure)
            # This is more for elements contained within a spatial zone, not necessarily the zone itself decomposing
            # but useful to list elements within a space/storey etc.
            # For now, focusing on decomposition for hierarchy. Elements are extracted separately.

            return item

        project = ifc_file.by_type("IfcProject")
        if project:
            spatial_structure_info["hierarchy"].append(build_hierarchy(project[0], "Project"))

        return spatial_structure_info


    def extract_building_elements(self, ifc_file) -> List[Dict]:
        elements = []
        # Common structural IFC types for bridges (can be expanded)
        bridge_element_types = [
            "IfcBeam", "IfcColumn", "IfcSlab", "IfcWall", "IfcFooting", "IfcFoundation",
            "IfcPlate", "IfcMember", "IfcStair", "IfcRailing", "IfcBuildingElementProxy",
            "IfcPile", "IfcBearing", "IfcTendon", "IfcReinforcingBar", "IfcReinforcingMesh"
        ]

        for ifc_type in bridge_element_types:
            for element in ifc_file.by_type(ifc_type):
                elem_info = self._get_element_basic_info(element)

                # Get properties
                elem_info["properties"] = []
                psets = ifcopenshell.util.element.get_psets(element, psets_only=False) # Includes qsets
                for pset_name, properties in psets.items():
                    prop_data = {"name": pset_name, "values": {}}
                    for prop_key, prop_value in properties.items():
                        prop_data["values"][prop_key] = prop_value
                    elem_info["properties"].append(prop_data)

                # Get material
                materials = ifcopenshell.util.element.get_material(element)
                if materials:
                    if hasattr(materials, 'ForLayerSet'): # IfcMaterialLayerSetUsage
                         elem_info["material"] = [ml.Material.Name for ml in materials.ForLayerSet.MaterialLayers] if materials.ForLayerSet else "LayerSet defined"
                    elif hasattr(materials, 'Material'): # Single material
                        elem_info["material"] = materials.Material.Name if materials.Material else "Material defined"
                    elif hasattr(materials, 'Name'): # Direct IfcMaterial
                        elem_info["material"] = materials.Name
                    else: # List of materials
                        elem_info["material"] = [m.Name for m in materials if hasattr(m, 'Name')]


                # Get quantity
                # Quantities are often in IfcElementQuantity
                # This can be complex due to different quantity types

                elements.append(elem_info)
        return elements

    def extract_materials_and_properties(self, ifc_file) -> List[Dict]:
        # This method could list all unique materials and their properties
        # or aggregate properties found across all elements.
        # For now, properties are extracted per element in extract_building_elements.
        # This method can be enhanced to provide a summary of all materials.

        all_materials = []
        unique_material_names = set()

        for material in ifc_file.by_type("IfcMaterial"):
            if material.Name not in unique_material_names:
                mat_info = {
                    "name": material.Name,
                    "description": material.Description if hasattr(material, 'Description') else None,
                    "category": material.Category if hasattr(material, 'Category') else None,
                    "properties": [] # Placeholder for specific material properties if directly associated
                }
                # Material properties might be linked via IfcMaterialProperties
                # For example, check material.HasProperties (inverse of IfcMaterialProperties.Material)
                all_materials.append(mat_info)
                unique_material_names.add(material.Name)

        # Also consider IfcMaterialList, IfcMaterialLayerSet, IfcMaterialLayerSetUsage, IfcMaterialConstituentSet
        # The current element extraction captures materials associated with elements.
        # This function can be a global list of defined materials.
        return all_materials


    def extract_geometric_representations(self, ifc_file) -> List[Dict]:
        # This can be very detailed. For now, let's provide a summary or count.
        # A full extraction would involve parsing IfcShapeRepresentation and its items.
        geometry_summary = []
        for element in ifc_file.by_type("IfcProduct"): # IfcProduct is the base for elements with geometry
            if element.Representation:
                geom_info = {
                    "element_id": element.GlobalId,
                    "element_type": element.is_a(),
                    "representations": []
                }
                for rep in element.Representation.Representations:
                    rep_data = {
                        "identifier": rep.RepresentationIdentifier,
                        "type": rep.RepresentationType,
                        "item_count": len(rep.Items)
                        # Further details like coordinates, profiles, etc., would go here
                    }
                    geom_info["representations"].append(rep_data)
                if geom_info["representations"]: # only add if there are representations
                    geometry_summary.append(geom_info)
        return geometry_summary

if __name__ == '__main__':
    # Create a dummy IFC file for basic testing
    # This requires a valid IFC file. For now, we'll assume one exists for testing.
    # Example: parser = IFCParserService()
    # results = parser.parse_ifc_file("path/to/your/testfile.ifc")
    # import json
    # print(json.dumps(results, indent=2))

    # Due to the sandbox environment, creating a dummy IFC file programmatically
    # with ifcopenshell to test here is non-trivial and might require more setup.
    # We will rely on unit/integration tests with actual sample IFC files later.
    print("IFCParserService defined. Ready for integration and testing with sample IFC files.")
