import json
import csv
from typing import List, Dict, Any
import os

# Import other services (assuming they are in the same directory or accessible via PYTHONPATH)
# from .training_data_generator import TrainingDataGenerator # Causes circular import if TrainingDataGenerator also imports this
# from .data_quality_controller import DataQualityController # Causes circular import

# For RDFLib, if it's used directly for RDF/JSON-LD generation beyond simple dicts
try:
    from rdflib import Graph, URIRef, Literal, Namespace
    from rdflib.namespace import RDF, RDFS, XSD
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False
    print("Warning: rdflib not installed. RDF export functionalities will be limited.")


# Placeholder for actual TrainingDataGenerator and DataQualityController
# In a real app, these would be properly imported and initialized.
# To avoid circular dependencies if these services also use DataExportService,
# they might be passed during initialization or accessed via a central service registry.
class PlaceholderTrainingDataGenerator:
    def generate_knowledge_triples(self, format_type: str = "rdf", limit: int = 10) -> List[Dict]:
        print(f"Placeholder: Generating {limit} knowledge triples for {format_type}")
        return [{"subject": f"s{i}", "predicate": f"p{i}", "object": f"o{i}"} for i in range(limit)]
    # Add other generation methods if needed by create_export_package directly

class PlaceholderDataQualityController:
    def score_data_quality(self, data: List[Dict], data_type: str = "generic") -> Dict:
        print(f"Placeholder: Scoring quality for {len(data)} items of type {data_type}")
        return {"overall_score": 4.5, "accuracy": 4.2, "completeness": 4.8, "notes": "Placeholder scores"}
    def generate_quality_report(self, quality_scores: Dict) -> str:
        print("Placeholder: Generating quality report")
        return "This is a placeholder quality report.\nScores: " + json.dumps(quality_scores)


class DataExportService:
    def __init__(self, output_dir: str = "exports"):
        # These would normally be injected or resolved via a service locator
        self.data_generator = PlaceholderTrainingDataGenerator()
        self.quality_controller = PlaceholderDataQualityController()
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        print(f"DataExportService initialized. Output directory: {self.output_dir}")

    def _get_full_path(self, file_path: str) -> str:
        """Ensures the file_path is within the configured output directory."""
        # Remove leading slashes from file_path to prevent absolute paths
        base_name = os.path.basename(file_path)
        return os.path.join(self.output_dir, base_name)

    def export_to_jsonl(self, data: List[Dict], file_path: str) -> str:
        """
        Exports data to JSONL format (LLM fine-tuning specific).
        Each line is a JSON object: {"instruction": "", "input": "", "output": ""}
        The 'data' input should be pre-formatted to fit this structure or adaptable.
        This example assumes 'data' items are dicts that can be directly written,
        or contain 'instruction', 'input', 'output' keys. If not, transformation is needed.
        """
        full_file_path = self._get_full_path(file_path)
        print(f"Exporting {len(data)} items to JSONL: {full_file_path}")
        try:
            with open(full_file_path, 'w', encoding='utf-8') as f:
                for item in data:
                    # Basic check: if item has the expected keys, use them directly
                    if all(k in item for k in ("instruction", "input", "output")):
                         json.dump(item, f)
                    else:
                        # Fallback: dump the item as is, assuming it's a single record for the line
                        # This might not be the desired format for all LLM fine-tuning scripts.
                        # A more robust version would transform 'item' to the I/O/O structure.
                        # Example naive transformation if data is QA pairs:
                        if "question" in item and "answer" in item:
                            transformed_item = {
                                "instruction": item.get("question"),
                                "input": "", # Input can be empty if instruction has all context
                                "output": item.get("answer")
                            }
                            json.dump(transformed_item, f)
                        else: # Just dump the raw item if no clear transformation
                            json.dump(item, f)
                    f.write('\n')
            print(f"Successfully exported to JSONL: {full_file_path}")
            return full_file_path
        except IOError as e:
            print(f"Error exporting to JSONL: {e}")
            raise

    def export_to_json_ld(self, triples: List[Dict], file_path: str, context: Dict = None) -> str:
        """
        Exports knowledge triples to JSON-LD format.
        'triples' should be a list of {"subject": s, "predicate": p, "object": o} dicts.
        A basic '@context' is provided if none is given.
        """
        full_file_path = self._get_full_path(file_path)
        print(f"Exporting {len(triples)} triples to JSON-LD: {full_file_path}")

        if not RDFLIB_AVAILABLE:
            # Fallback to basic JSON if rdflib is not available
            print("Warning: rdflib not available. Exporting as simple JSON list of triples, not true JSON-LD graph.")
            output_data = {"@graph": triples}
            if context:
                 output_data["@context"] = context
            try:
                with open(full_file_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2)
                print(f"Successfully exported basic JSON (simulating JSON-LD): {full_file_path}")
                return full_file_path
            except IOError as e:
                print(f"Error exporting to basic JSON: {e}")
                raise

        # Using rdflib for proper JSON-LD
        g = Graph()
        # Example default context - this should be tailored to the ontology
        default_context = context or {
            "rdf": str(RDF),
            "rdfs": str(RDFS),
            "xsd": str(XSD),
            "ex": "http://example.org/bridge#" # Example namespace
        }
        # Bind namespaces for cleaner output if prefixes are used in triples
        for prefix, ns_uri in default_context.items():
            if isinstance(ns_uri, str) and (ns_uri.startswith("http://") or ns_uri.startswith("https://")):
                 g.bind(prefix, Namespace(ns_uri))

        EX = Namespace(default_context.get("ex", "http://example.org/bridge#"))

        for triple in triples:
            s = URIRef(EX[triple["subject"]]) if isinstance(triple["subject"], str) and not triple["subject"].startswith("http") else URIRef(triple["subject"])
            p = URIRef(EX[triple["predicate"]]) if isinstance(triple["predicate"], str) and not triple["predicate"].startswith("http") else URIRef(triple["predicate"])

            obj_val = triple["object"]
            if isinstance(obj_val, str):
                # Check if object is likely a URI or a literal
                if obj_val.startswith("http://") or obj_val.startswith("https://") or ":" in obj_val.split()[0] : # crude check for prefixed name
                    o = URIRef(EX[obj_val]) if not obj_val.startswith("http") and ":" not in obj_val.split()[0] else URIRef(obj_val)
                else:
                    o = Literal(obj_val)
            elif isinstance(obj_val, (int, float, bool)):
                 o = Literal(obj_val)
            else: # Default to string literal
                 o = Literal(str(obj_val))
            g.add((s, p, o))

        try:
            # Serialize to JSON-LD string
            json_ld_data = g.serialize(format="json-ld", context=default_context, indent=2)
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(json_ld_data)
            print(f"Successfully exported to JSON-LD: {full_file_path}")
            return full_file_path
        except Exception as e: # Catch rdflib specific errors if any
            print(f"Error exporting to JSON-LD using rdflib: {e}")
            raise

    def export_to_csv(self, data: List[Dict], file_path: str) -> str:
        """
        Exports data (list of flat dictionaries) to CSV format.
        Assumes all dicts in 'data' have the same keys for the header.
        """
        full_file_path = self._get_full_path(file_path)
        print(f"Exporting {len(data)} items to CSV: {full_file_path}")
        if not data:
            print("No data to export to CSV.")
            # Create an empty file or raise error? For now, empty file.
            open(full_file_path, 'w').close()
            return full_file_path

        try:
            # Use keys from the first item as header
            headers = list(data[0].keys())
            with open(full_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            print(f"Successfully exported to CSV: {full_file_path}")
            return full_file_path
        except IOError as e:
            print(f"Error exporting to CSV: {e}")
            raise
        except Exception as e: # Catch other potential errors like inconsistent dict keys
            print(f"An unexpected error occurred during CSV export: {e}")
            raise


    def export_to_rdf_turtle(self, triples: List[Dict], file_path: str) -> str:
        """
        Exports knowledge triples to RDF Turtle format.
        'triples' should be a list of {"subject": s, "predicate": p, "object": o} dicts.
        Requires rdflib.
        """
        full_file_path = self._get_full_path(file_path)
        print(f"Exporting {len(triples)} triples to RDF Turtle: {full_file_path}")

        if not RDFLIB_AVAILABLE:
            print("Error: rdflib is not available, cannot export to RDF Turtle.")
            raise ImportError("rdflib library is required for RDF Turtle export.")

        g = Graph()
        EX = Namespace("http://example.org/bridge#") # Example namespace
        g.bind("ex", EX)
        g.bind("rdf", RDF)
        g.bind("rdfs", RDFS)

        for triple in triples:
            s = URIRef(EX[triple["subject"]]) if isinstance(triple["subject"], str) and not triple["subject"].startswith("http") else URIRef(triple["subject"])
            p = URIRef(EX[triple["predicate"]]) if isinstance(triple["predicate"], str) and not triple["predicate"].startswith("http") else URIRef(triple["predicate"])

            obj_val = triple["object"]
            if isinstance(obj_val, str):
                if obj_val.startswith("http://") or obj_val.startswith("https://") or ":" in obj_val.split()[0]:
                    o = URIRef(EX[obj_val]) if not obj_val.startswith("http") and ":" not in obj_val.split()[0] else URIRef(obj_val)
                else:
                    o = Literal(obj_val)
            elif isinstance(obj_val, (int, float, bool)):
                 o = Literal(obj_val)
            else:
                 o = Literal(str(obj_val))
            g.add((s, p, o))

        try:
            turtle_data = g.serialize(format="turtle")
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(turtle_data)
            print(f"Successfully exported to RDF Turtle: {full_file_path}")
            return full_file_path
        except Exception as e:
            print(f"Error exporting to RDF Turtle: {e}")
            raise

    def create_export_package(self, export_config: Dict, data_to_export: List[Dict] = None) -> Dict:
        """
        Creates a complete export package.
        Includes: data file(s), metadata, quality report, usage instructions.
        'export_config' dict specifies what to generate and export.
        Example config:
        {
            "data_type": "qa_pairs", # or "entity_descriptions", "knowledge_triples", "technical_scenarios"
            "generation_params": {"entity_types": ["Bridge"], "limit": 100}, # Used if data_to_export is None
            "export_formats": ["jsonl", "csv"],
            "package_name": "bridge_qa_export_v1"
        }

        Args:
            export_config (Dict): Configuration for the export.
            data_to_export (Optional[List[Dict]]): Pre-generated data to export.
                                                   If None, data will be generated based on export_config.
        """
        package_name = export_config.get("package_name", "training_data_export")
        package_dir = os.path.join(self.output_dir, package_name)
        if not os.path.exists(package_dir):
            os.makedirs(package_dir)

        print(f"Creating export package: {package_name} in {package_dir}")

        data_type = export_config.get("data_type", "knowledge_triples")
        actual_data_to_process: List[Dict]
        gen_params = export_config.get("generation_params", {}) # Initialize gen_params

        if data_to_export is not None:
            actual_data_to_process = data_to_export
            print(f"Using pre-generated data for package: {len(actual_data_to_process)} items of type {data_type}.")
            # Update gen_params to reflect pre-generated source for metadata
            gen_params["source"] = "pre_generated"
            gen_params["original_count"] = len(actual_data_to_process)
        else:
            # 1. Generate Data (using self.data_generator placeholder)
            # gen_params is already initialized from export_config
            print(f"No pre-generated data provided. Generating data for type '{data_type}' with params: {gen_params}")

            if data_type == "qa_pairs":
                # Assuming self.data_generator has a generate_qa_pairs_from_graph method
                # For the placeholder, it might not use all gen_params, but real one would.
                actual_data_to_process = self.data_generator.generate_qa_pairs_from_graph(**gen_params)
            elif data_type == "entity_descriptions":
                 actual_data_to_process = self.data_generator.generate_entity_descriptions(**gen_params)
            elif data_type == "knowledge_triples":
                actual_data_to_process = self.data_generator.generate_knowledge_triples(**gen_params)
            # Add other data types as self.data_generator (placeholder or real) supports them
            # elif data_type == "technical_scenarios":
            #    actual_data_to_process = self.data_generator.generate_technical_scenarios(**gen_params)
            else:
                print(f"Warning: Unknown data_type '{data_type}' for internal generation. Generating generic triples as fallback.")
                actual_data_to_process = self.data_generator.generate_knowledge_triples(**gen_params) # Fallback to triples
            print(f"Internally generated {len(actual_data_to_process)} items.")

        if not actual_data_to_process: # Check if list is empty
            print(f"No data available for package '{package_name}' (type: {data_type}). Aborting package creation for this type.")
            return {
                "package_location": package_dir,
                "files_generated": [],
                "metadata": {"error": "No data to process or generate", "package_name": package_name, "data_type": data_type},
                "message": "No data processed for package."
            }

        # 2. Quality Control
        quality_scores = self.quality_controller.score_data_quality(actual_data_to_process, data_type=data_type)
        quality_report_str = self.quality_controller.generate_quality_report(quality_scores)

        report_path = os.path.join(package_dir, "quality_report.txt")
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(quality_report_str)
            print(f"Quality report saved to: {report_path}")
        except IOError as e:
            print(f"Error saving quality report: {e}")

        # 3. Export Data in specified formats
        exported_file_paths = []
        for fmt in export_config.get("export_formats", ["jsonl"]):
            file_name = f"{data_type}_data.{fmt}"
            # Use package_dir for these files, not self.output_dir directly
            output_file_path = os.path.join(package_dir, file_name) # Corrected to use package_dir

            try:
                if fmt == "jsonl":
                    self.export_to_jsonl(actual_data_to_process, output_file_path)
                elif fmt == "csv":
                    self.export_to_csv(actual_data_to_process, output_file_path)
                elif fmt == "json_ld":
                    # JSON-LD typically for triples. If data is not triples, it needs transformation.
                    if data_type == "knowledge_triples":
                         self.export_to_json_ld(actual_data_to_process, output_file_path)
                    else:
                         print(f"Warning: JSON-LD export is best for triples. Data type is {data_type}. Exporting as plain JSON list.")
                         # Fallback: simple JSON dump if not triples.
                         with open(output_file_path, 'w', encoding='utf-8') as f_json:
                            json.dump(actual_data_to_process, f_json, indent=2)
                elif fmt == "rdf_turtle":
                    if data_type == "knowledge_triples":
                        self.export_to_rdf_turtle(actual_data_to_process, output_file_path)
                    else:
                        print(f"Warning: RDF Turtle export is for triples. Data type is {data_type}. Skipping.")
                        continue # Skip if not applicable
                else:
                    print(f"Warning: Unknown export format '{fmt}'. Skipping.")
                    continue
                exported_file_paths.append(output_file_path)
            except Exception as e:
                print(f"Error exporting data to {fmt}: {e}")


        # 4. Create Metadata file
        metadata = {
            "package_name": package_name,
            "data_type": data_type,
            "generation_parameters": gen_params, # This now includes source: "pre_generated" if applicable
            "export_formats_requested": export_config.get("export_formats"),
            "exported_files": [os.path.basename(p) for p in exported_file_paths], # Store relative paths
            "num_records": len(actual_data_to_process),
            "quality_assessment": quality_scores,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
        }
        metadata_path = os.path.join(package_dir, "metadata.json")
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            print(f"Metadata file saved to: {metadata_path}")
        except IOError as e:
            print(f"Error saving metadata file: {e}")

        # 5. Create Usage Instructions (simple README)
        readme_content = f"""# Export Package: {package_name}

## Contents:
- Data files: {', '.join([os.path.basename(p) for p in exported_file_paths])}
- metadata.json: Contains details about the generation and contents of this package.
- quality_report.txt: Provides an assessment of the data quality.

## Data Type:
{data_type}

## Usage:
Refer to the specific file formats for instructions on how to use them.
- JSONL files are often used for fine-tuning Large Language Models. Each line is a JSON object.
- CSV files can be opened with spreadsheet software or parsed programmatically.
- JSON-LD and RDF Turtle files are standard semantic web formats for knowledge graph data.

Please review the quality_report.txt and metadata.json for more information.
"""
        readme_path = os.path.join(package_dir, "README.md")
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"README file saved to: {readme_path}")
        except IOError as e:
            print(f"Error saving README file: {e}")

        print(f"Export package '{package_name}' created successfully at {package_dir}")
        return {
            "package_location": package_dir,
            "files_generated": [os.path.basename(p) for p in exported_file_paths] + ["metadata.json", "quality_report.txt", "README.md"],
            "metadata": metadata
        }


if __name__ == '__main__':
    # Example Usage (for testing purposes)
    export_service = DataExportService(output_dir="temp_exports") # Use a temp directory for testing

    # --- Test individual export functions ---
    sample_data_qa = [
        {"instruction": "What is a suspension bridge?", "input": "", "output": "A bridge where the deck is hung below suspension cables."},
        {"instruction": "Explain bridge resonance.", "input": "Caused by wind or traffic.", "output": "Oscillation of bridge components at their natural frequency."}
    ]
    sample_triples = [
        {"subject": "GoldenGateBridge", "predicate": "type", "object": "SuspensionBridge"},
        {"subject": "GoldenGateBridge", "predicate": "locatedIn", "object": "SanFrancisco"},
        {"subject": "BrooklynBridge", "predicate": "type", "object": "HybridCableStayedSuspensionBridge"},
        {"subject": "BrooklynBridge", "predicate": "crosses", "object": "EastRiver"}
    ]
    sample_generic_data = [
        {"id": 1, "name": "Item A", "value": 100},
        {"id": 2, "name": "Item B", "value": 200}
    ]

    print("\n--- Testing JSONL Export ---")
    export_service.export_to_jsonl(sample_data_qa, "qa_data.jsonl")

    print("\n--- Testing CSV Export ---")
    export_service.export_to_csv(sample_generic_data, "generic_data.csv")

    if RDFLIB_AVAILABLE:
        print("\n--- Testing JSON-LD Export ---")
        export_service.export_to_json_ld(sample_triples, "knowledge_graph.jsonld", context={"ex": "http://example.org/bridge#", "type": "@type"})

        print("\n--- Testing RDF Turtle Export ---")
        export_service.export_to_rdf_turtle(sample_triples, "knowledge_graph.ttl")
    else:
        print("\n--- Skipping RDFLib dependent exports (JSON-LD full, RDF Turtle) ---")
        print("--- Testing JSON-LD Export (basic JSON fallback) ---")
        export_service.export_to_json_ld(sample_triples, "knowledge_graph_basic.jsonld", context={"ex": "http://example.org/bridge#", "type": "@type"})


    # --- Test package creation ---
    print("\n--- Testing Export Package Creation ---")
    export_config_qa = {
        "data_type": "qa_pairs",
        "generation_params": {"limit": 20}, # Small limit for testing
        "export_formats": ["jsonl", "csv"],
        "package_name": "bridge_qa_package_test_v1"
    }
    package_info_qa = export_service.create_export_package(export_config_qa)
    # print(json.dumps(package_info_qa, indent=2))

    if RDFLIB_AVAILABLE:
        export_config_kg = {
            "data_type": "knowledge_triples",
            "generation_params": {"limit": 15}, # Small limit for testing
            "export_formats": ["json_ld", "rdf_turtle", "csv"], # CSV for triples might be simple s,p,o
            "package_name": "bridge_kg_package_test_v1"
        }
        package_info_kg = export_service.create_export_package(export_config_kg)
        # print(json.dumps(package_info_kg, indent=2))
    else:
        print("\n--- Skipping KG package test that relies heavily on RDFLib for all formats ---")
        export_config_kg_basic = {
            "data_type": "knowledge_triples",
            "generation_params": {"limit": 15},
            "export_formats": ["json_ld"], # Will use basic JSON-LD
            "package_name": "bridge_kg_package_test_basic_v1"
        }
        package_info_kg_basic = export_service.create_export_package(export_config_kg_basic)


    print("\n--- Example service usage finished. Check 'temp_exports' directory. ---")
    # Clean up temp_exports directory after manual check if needed
    # import shutil
    # shutil.rmtree("temp_exports")
