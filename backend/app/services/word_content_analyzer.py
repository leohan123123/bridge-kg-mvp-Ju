from typing import Dict, List, Any
import re

# Attempt to import the actual BridgeEntityExtractor
# If it fails, fall back to a mock version for standalone development/testing.
try:
    from .bridge_entity_extractor import BridgeEntityExtractor
    print("Successfully imported BridgeEntityExtractor.")
except ImportError:
    print("Warning: BridgeEntityExtractor not found. Using MockBridgeEntityExtractor for WordContentAnalyzer.")
    class MockBridgeEntityExtractor:
        def extract_entities(self, text: str) -> Dict[str, List[str]]:
            entities = {"materials": [], "processes": [], "specifications": [], "components": [], "parameters": []}
            if "concrete" in text.lower(): entities["materials"].append("Concrete")
            if "steel" in text.lower(): entities["materials"].append("Steel")
            if "welding" in text.lower(): entities["processes"].append("Welding")
            if "beam" in text.lower(): entities["components"].append("Beam")

            # Simple ASTM code extraction
            astm_codes = re.findall(r"ASTM\s+[A-Z0-9]+(?:-[0-9]+)?", text, re.IGNORECASE)
            if astm_codes: entities["specifications"].extend(astm_codes)

            # Simple parameter extraction like "strength of 50 MPa"
            param_matches = re.findall(r"(\w+\s*(?:strength|modulus|density|grade|size))\s*(?:of|is|:|)\s*([0-9]+\.?[0-9]*\s*\w+)", text, re.IGNORECASE)
            for match in param_matches:
                entities["parameters"].append(f"{match[0].strip()}: {match[1].strip()}")
            return entities

        def extract_relations(self, text: str, entities: Dict[str, List[str]]) -> List[Dict[str, Any]]:
            relations = []
            if "Concrete" in entities.get("materials", []) and "Beam" in entities.get("components", []):
                if "concrete beam" in text.lower():
                    relations.append({"source": "Beam", "target": "Concrete", "type": "madeOfMaterial"})

            for spec in entities.get("specifications", []):
                if "steel" in spec.lower() or ("steel" in text.lower() and spec in text): # very basic association
                    relations.append({"source": "Steel", "target": spec, "type": "conformsToStandard"})
            return relations

    BridgeEntityExtractor = MockBridgeEntityExtractor


class WordContentAnalyzer:
    def __init__(self):
        self.bridge_extractor = BridgeEntityExtractor()

    def _extract_common_entities_relations(self, text: str) -> Dict[str, Any]:
        """Helper to extract common entities and relations."""
        entities = self.bridge_extractor.extract_entities(text)
        relations = self.bridge_extractor.extract_relations(text, entities)
        return {"extracted_entities": entities, "extracted_relations": relations}

    def analyze_technical_standard(self, content: Dict, sections_data: Dict = None) -> Dict:
        """
        Analyzes content from a technical standard document.
        'content' is from WordParserService.extract_text_content
        'sections_data' (optional) is from WordParserService.extract_headers_and_sections
        """
        full_text = content.get("text", "")
        analysis_results = {
            "document_type_guess": "Technical Standard", # Initial guess
            "clauses": [],
            "technical_requirements": [],
            "parameter_indicators": [], # These might be text based, separate from table params
            **self._extract_common_entities_relations(full_text)
        }

        # Clause identification (条文) using sections_data if available, or regex on full_text
        if sections_data:
            def find_clauses_in_sections(current_sections_dict, prefix=""):
                clauses_found = []
                for title, data in current_sections_dict.items():
                    # Common patterns: "第X条", "X.Y.Z", specific keywords in title
                    clause_match = re.match(r"^(?:第\s*\d+\s*条)|(?:[A-Z]?\d+(?:\.\d+)*)|(?:Chapter\s\d+)|(?:Section\s\d+)", title, re.IGNORECASE)
                    is_clause_title = bool(clause_match)

                    full_title_path = f"{prefix}{title}" if prefix else title

                    if is_clause_title:
                        clauses_found.append({
                            "title": full_title_path,
                            "level": data.get("level"),
                            "content_preview": (" ".join(data.get("paragraphs", [])))[:150] + "..."
                        })
                    # Recursively check subheadings
                    if "subheadings" in data and data["subheadings"]:
                        clauses_found.extend(find_clauses_in_sections(data["subheadings"], prefix=f"{full_title_path} / "))
                return clauses_found
            analysis_results["clauses"] = find_clauses_in_sections(sections_data)
        else: # Fallback to regex on full text if sections_data is not provided
            # This is less accurate as it doesn't understand structure.
            # Example: find lines starting with typical clause numbering.
            for line in full_text.splitlines():
                if re.match(r"^\s*(?:第\s*\d+\s*条)|(?:[A-Z]?\d+(?:\.\d+){1,})\s+.*", line):
                    analysis_results["clauses"].append({"title": line.strip(), "level": None, "content_preview": ""})


        # Technical requirements (技术要求) - sentences with modal verbs like "shall", "must", "应", "须"
        # Using a more robust sentence splitting regex
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', full_text)
        for sentence in sentences:
            if re.search(r"\b(shall|must|should|is to be|are to be|应|须|必须|规定)\b", sentence, re.IGNORECASE):
                analysis_results["technical_requirements"].append(sentence.strip())

        # Parameter indicators (参数指标) from text - e.g., "The minimum yield strength is 250 MPa."
        # This can be enhanced by NER for parameters.
        # Using the parameter extraction from BridgeEntityExtractor as a starting point.
        if "parameters" in analysis_results["extracted_entities"]:
             analysis_results["parameter_indicators"] = analysis_results["extracted_entities"]["parameters"]

        return analysis_results

    def analyze_design_specification(self, content: Dict, sections_data: Dict = None) -> Dict:
        """Analyzes content from a design specification document."""
        full_text = content.get("text", "")
        analysis_results = {
            "document_type_guess": "Design Specification",
            "design_methods": [],
            "calculation_formulas": [], # Store as text snippets or identified equations
            "design_parameters": [], # Specific parameters used in design
            **self._extract_common_entities_relations(full_text)
        }

        # Design Methods (e.g., LRFD, ASD)
        known_methods = ["LRFD", "Load and Resistance Factor Design", "ASD", "Allowable Stress Design", "Limit State Design", "AASHTO"]
        for method in known_methods:
            if re.search(r"\b" + re.escape(method) + r"\b", full_text, re.IGNORECASE):
                analysis_results["design_methods"].append(method)

        # Calculation Formulas (look for equation-like patterns or keywords)
        # This is highly heuristic. True formula extraction is complex (MathML, LaTeX, OCR for images).
        # Regex for something that looks like "Var = ...math..." or keywords
        formula_keywords = ["formula", "equation", "计算公式", "表达式"]
        potential_formulas = []
        lines = full_text.splitlines()
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in formula_keywords):
                potential_formulas.append(line.strip())
            # Simple pattern: A = B or A=B*C etc. (very naive)
            elif re.match(r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=.*[+\-*/^()].*", line):
                 potential_formulas.append(line.strip())
            # If previous line had a formula indicator
            elif i > 0 and any(kw in lines[i-1].lower() for kw in formula_keywords) and line.strip() and not any(kw in line.lower() for kw in formula_keywords):
                 potential_formulas.append(lines[i-1].strip() + " " + line.strip())


        analysis_results["calculation_formulas"] = list(set(potential_formulas))[:10] # Limit for brevity

        # Design Parameters (often mentioned near formulas or in specific sections)
        # Could be similar to parameter_indicators but more context-specific
        # Using the general parameter extraction for now
        if "parameters" in analysis_results["extracted_entities"]:
             analysis_results["design_parameters"] = analysis_results["extracted_entities"]["parameters"]

        return analysis_results

    def analyze_construction_manual(self, content: Dict, sections_data: Dict = None) -> Dict:
        """Analyzes content from a construction manual document."""
        full_text = content.get("text", "")
        analysis_results = {
            "document_type_guess": "Construction Manual",
            "process_flows": [], # Descriptions of sequences of operations
            "quality_standards": [], # Specific quality checks or criteria
            "operating_procedures": [], # Step-by-step instructions
            **self._extract_common_entities_relations(full_text)
        }

        # Process Flows (工艺流程) - look for steps, sequences
        # Keywords: "step", "procedure", "sequence", "workflow", "工艺流程", "步骤"
        # Often found in sections or lists.
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', full_text)
        for sent in sentences:
            if re.search(r"\b(step\s*\d+|procedure|sequence|workflow|工艺流程|步骤)\b", sent, re.IGNORECASE):
                analysis_results["process_flows"].append(sent.strip())

        # Quality Standards (质量标准)
        # Keywords: "quality control", "inspection", "acceptance criteria", "tolerance", "质量标准", "检验", "验收"
        for sent in sentences:
            if re.search(r"\b(quality\scontrol|inspection|acceptance\scriteria|tolerance|质量标准|检验|验收)\b", sent, re.IGNORECASE):
                analysis_results["quality_standards"].append(sent.strip())

        # Operating Procedures (操作规程)
        # Keywords: "operation", "instruction", "guideline", "safety precaution", "操作规程", "指南", "安全须知"
        for sent in sentences:
            if re.search(r"\b(operation|instruction|guideline|safety\sprecaution|操作规程|指南|安全须知)\b", sent, re.IGNORECASE):
                analysis_results["operating_procedures"].append(sent.strip())

        return analysis_results

    def extract_technical_parameters(self, tables: List[Dict]) -> Dict:
        """
        Extracts technical parameters from tables.
        'tables' is the output from WordParserService.extract_tables.
        """
        extracted_params_by_category = {
            "material_properties": [], # E.g., {"parameter_name": "Yield Strength", "value": "350 MPa", "material": "Steel Grade X"}
            "geometric_dimensions": [],# E.g., {"component": "Beam A", "parameter_name": "Height", "value": "1200 mm"}
            "load_specifications": [], # E.g., {"load_type": "Dead Load", "value": "5 kN/m^2"}
            "generic_parameters": []   # Other parameters not easily categorized
        }

        # Keywords for categorization
        material_kws = ["material", "grade", "strength", "modulus", "density", "yield", "tensile", "compressive", "材料", "强度", "模量", "密度"]
        dimension_kws = ["dimension", "size", "height", "width", "length", "thickness", "diameter", "radius", "尺寸", "规格", "高度", "宽度", "长度", "厚度", "直径", "半径"]
        load_kws = ["load", "capacity", "pressure", "force", "moment", "stress", "荷载", "承载力", "压力", "力", "弯矩", "应力"]

        unit_pattern = r"\b([0-9]+\.?[0-9]*)\s*([a-zA-Zμ%/°]+[0-9²³]*)\b" # Matches "100 MPa", "20 mm", "50 %" etc.

        for table_info in tables:
            if table_info.get("error"): continue
            table_data = table_info.get("data", [])
            if not table_data or len(table_data) < 2: continue # Need at least a header and a data row

            headers = [str(h).strip().lower() for h in table_data[0]]

            for row_idx, row_data in enumerate(table_data[1:], start=1): # Skip header
                row_dict = {} # Parameter-value pairs for current row based on headers
                parameter_name_candidate = None
                value_candidate = None
                unit_candidate = None

                # First column often contains the parameter name or item
                if headers:
                    parameter_name_candidate = str(row_data[0]).strip() if row_data else None

                for col_idx, cell_text_str in enumerate(row_data):
                    cell_text_str = str(cell_text_str).strip()
                    header = headers[col_idx] if col_idx < len(headers) else ""

                    # Try to extract value and unit
                    match_unit = re.search(unit_pattern, cell_text_str)
                    if match_unit:
                        value_candidate = match_unit.group(1)
                        unit_candidate = match_unit.group(2)
                        # The part before value might be the parameter name if not in first col
                        if not parameter_name_candidate and cell_text_str.replace(match_unit.group(0), "").strip():
                             parameter_name_candidate = cell_text_str.replace(match_unit.group(0), "").strip()
                        elif not parameter_name_candidate and header: # Use header if cell is just value+unit
                             parameter_name_candidate = header.replace("value","").replace("值","").strip()


                    # If we have a parameter name and a value
                    if parameter_name_candidate and value_candidate:
                        param_entry = {
                            "parameter_name": parameter_name_candidate,
                            "value": value_candidate,
                            "unit": unit_candidate if unit_candidate else "N/A",
                            "table_source": {"index": table_info.get("table_index"), "row": row_idx, "header": header}
                        }

                        # Categorize
                        combined_text_for_cat = (parameter_name_candidate + " " + header).lower()
                        if any(kw in combined_text_for_cat for kw in material_kws):
                            extracted_params_by_category["material_properties"].append(param_entry)
                        elif any(kw in combined_text_for_cat for kw in dimension_kws):
                            extracted_params_by_category["geometric_dimensions"].append(param_entry)
                        elif any(kw in combined_text_for_cat for kw in load_kws):
                            extracted_params_by_category["load_specifications"].append(param_entry)
                        else:
                            extracted_params_by_category["generic_parameters"].append(param_entry)

                        # Reset for next potential parameter in the same row if table is wide
                        parameter_name_candidate = None
                        value_candidate = None
                        unit_candidate = None

                # If the row had a parameter name in the first col, and other cols are values for it
                # This part needs more sophisticated row interpretation logic (e.g. if a row is "Prop | Val1 | Val2 | Val3")

        return extracted_params_by_category

    def identify_document_type(self, text_content_dict: Dict, tables: List[Dict], sections: Dict = None) -> str:
        """
        Identifies document type (Technical Standard, Design Specification, Construction Manual)
        based on keywords, structure, and table content.
        """
        full_text = text_content_dict.get("text", "").lower()
        metadata = text_content_dict.get("metadata", {})
        title = metadata.get("title", "").lower() if metadata.get("title") else ""

        scores = {"Technical Standard": 0.0, "Design Specification": 0.0, "Construction Manual": 0.0}

        # Keywords and weights
        # (Higher weight for title matches)
        keyword_map = {
            "Technical Standard": [("standard", 2), ("code", 2), ("specification", 1.5), ("guideline", 1), ("regulation", 1), ("norm", 1), ("条文", 2), ("规范", 2), ("标准", 2), ("规程", 1.5), ("指南", 1), ("shall", 0.5), ("must", 0.5), ("应", 0.5), ("须", 0.5)],
            "Design Specification": [("design", 2), ("calculation", 1.5), ("formula", 1), ("method", 1), ("analysis", 1), ("设计", 2), ("计算", 1.5), ("公式", 1), ("aashto", 1.5), ("lrfd", 1.5), ("eurocode", 1.5)],
            "Construction Manual": [("manual", 2), ("construction", 1.5), ("procedure", 1), ("installation", 1), ("operation", 1), ("safety", 1), ("maintenance", 1), ("施工", 2), ("手册", 2), ("安装", 1), ("操作", 1), ("工艺流程", 1.5), ("step-by-step", 1)]
        }

        for doc_type, kws_with_weights in keyword_map.items():
            for kw, weight in kws_with_weights:
                if f" {kw} " in f" {title} ": # Higher weight for title
                    scores[doc_type] += weight * 1.5
                if f" {kw} " in f" {full_text} ":
                    scores[doc_type] += weight

        # Structural clues from sections (if available)
        if sections:
            flat_section_titles = []
            def get_all_titles(s_dict):
                titles = []
                for t, d in s_dict.items():
                    titles.append(t.lower())
                    if "subheadings" in d: titles.extend(get_all_titles(d["subheadings"]))
                return titles
            flat_section_titles = get_all_titles(sections)

            if any("appendix" in t for t in flat_section_titles) or any("annex" in t for t in flat_section_titles):
                scores["Technical Standard"] += 1 # Appendices are common in standards

        # Table content clues (very basic)
        for table in tables:
            if table.get("error"): continue
            table_flat_text = " ".join(" ".join(map(str,r)) for r in table.get("data", [])).lower()
            if "parameter" in table_flat_text and "value" in table_flat_text:
                 scores["Technical Standard"] += 0.5
                 scores["Design Specification"] += 0.5


        # Determine best type
        if not any(s > 0 for s in scores.values()): return "Unknown"

        # Normalize scores (optional, if using probabilities)
        # sorted_types = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]

        # Confidence check
        if max_score < 2.0: # Minimum confidence threshold
            # Check if other scores are very close
            # For example, if top two scores are within 0.5 of each other, could be "General/Mixed"
            sorted_scores = sorted(scores.values(), reverse=True)
            if len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1]) < 0.5 and sorted_scores[0] > 1.0 :
                 return "General Technical Document / Mixed Type"
            return "General Technical Document / Unknown" # Low confidence or no clear winner

        return best_type


# Example usage (for local testing)
if __name__ == '__main__':
    analyzer = WordContentAnalyzer()

    # Mock data for testing
    mock_text_content_std = {
        "text": "This is a Bridge Construction Standard. All steel components shall conform to ASTM A709. The design must follow the AASHTO LRFD specifications. 第1条 General. 第1.1 Scope.",
        "metadata": {"title": "Official Bridge Standard 2023"}
    }
    mock_sections_std = {
        "Official Bridge Standard 2023": {"level": 0, "paragraphs": [], "subheadings": {
            "第1条 General": {"level": 1, "paragraphs": ["Scope of the standard..."], "subheadings": {
                "1.1 Scope": {"level": 2, "paragraphs": ["Details of scope"], "subheadings": {}}
            }},
            "第2条 Materials": {"level": 1, "paragraphs": ["Material requirements..."], "subheadings": {}}
        }}
    }
    mock_tables_std = [{"data": [["Parameter", "Value"], ["Steel Grade", "50W (345W)"]], "table_index":0}]

    print("--- Analyzing Technical Standard (Mock) ---")
    analysis_std = analyzer.analyze_technical_standard(mock_text_content_std, sections_data=mock_sections_std)
    # print(f"  Analysis Result: {analysis_std}")
    print(f"  Clauses found: {len(analysis_std.get('clauses',[]))}")
    print(f"  Technical Requirements found: {len(analysis_std.get('technical_requirements',[]))}")
    print(f"  Entities (materials): {analysis_std.get('extracted_entities',{}).get('materials')}")


    print("\n--- Identifying Document Type (Mock Standard) ---")
    doc_type_std = analyzer.identify_document_type(mock_text_content_std, mock_tables_std, mock_sections_std)
    print(f"  Identified Type for Standard: {doc_type_std}")

    mock_text_content_design = {
        "text": "Structural Design Calculations for the Arch Bridge. Based on Eurocode 3. The main formula used for tension members is N_t_Rd = A_eff * f_y / gamma_M0. Design parameters are listed in Table 2.",
        "metadata": {"title": "Arch Bridge Design Report"}
    }
    mock_tables_design = [{"data": [["Parameter", "Value"], ["Live Load", "HS20-44"]], "table_index":0}]

    print("\n--- Analyzing Design Specification (Mock) ---")
    analysis_design = analyzer.analyze_design_specification(mock_text_content_design)
    print(f"  Design Methods: {analysis_design.get('design_methods')}")
    print(f"  Calculation Formulas (sample): {analysis_design.get('calculation_formulas',[])[:1]}")
    print(f"  Design Parameters (sample): {analysis_design.get('design_parameters',[])[:2]}")

    print("\n--- Identifying Document Type (Mock Design) ---")
    doc_type_design = analyzer.identify_document_type(mock_text_content_design, mock_tables_design)
    print(f"  Identified Type for Design: {doc_type_design}")


    print("\n--- Extracting Technical Parameters from Tables (Mock) ---")
    tables_for_params = [
        {"table_index": 0, "data": [
            ["Material Property", "Value", "Unit", "Standard"],
            ["Yield Strength (Steel)", "350", "MPa", "ASTM A709"],
            ["Compressive Strength (Concrete)", "40", "MPa", "ACI 318"]
        ]},
        {"table_index": 1, "data": [
            ["Component", "Dimension", "Value (mm)"],
            ["Girder Depth", "Overall", "1500"],
            ["Flange Width", "Top", "300"]
        ]}
    ]
    tech_params = analyzer.extract_technical_parameters(tables_for_params)
    # print(json.dumps(tech_params, indent=2))
    print(f"  Extracted Material Properties: {len(tech_params['material_properties'])}")
    print(f"  Extracted Geometric Dimensions: {len(tech_params['geometric_dimensions'])}")
    if tech_params['material_properties']:
        print(f"    Sample Material Prop: {tech_params['material_properties'][0]}")
    if tech_params['geometric_dimensions']:
        print(f"    Sample Geometric Dim: {tech_params['geometric_dimensions'][0]}")
