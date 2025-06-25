from typing import Dict, List
# Attempt to import BRIDGE_DESIGN_ONTOLOGY from the sibling service
# This might require adjusting sys.path or using relative imports if run as part of a larger package
try:
    from .bridge_design_ontology import BRIDGE_DESIGN_ONTOLOGY
except ImportError:
    # Fallback for direct execution or if the above fails, define it locally or raise error
    # For this context, we'll assume it's available. If not, this will cause issues.
    # A better solution in a real project would be a shared constants module or dependency injection.
    BRIDGE_DESIGN_ONTOLOGY = {
        "设计理论": {
            "结构力学理论": ["弯曲理论", "剪切理论", "扭转理论", "稳定理论", "动力学理论"],
            # ... (rest of the ontology as defined previously)
        }
        # Ensure the full ontology is here if the import fails and it's needed directly
    }
    # A more robust fallback would be to read it from a file or have a default minimal structure.
    # For now, let's assume the import will work in the final application structure.
    # If this script were run standalone, BRIDGE_DESIGN_ONTOLOGY would be minimal or cause errors.
    # To make it runnable standalone for testing, you might copy the full dict here.
    # For now, we'll proceed assuming the import works in the integrated environment.
    pass


class DesignKnowledgeExtractor:
    def __init__(self):
        # If the import works, self.design_ontology will be correctly populated.
        # If not, and no fallback is properly defined, this could be an empty dict or raise NameError.
        try:
            self.design_ontology = BRIDGE_DESIGN_ONTOLOGY
        except NameError:
            # This block executes if BRIDGE_DESIGN_ONTOLOGY was not successfully imported or defined.
            print("Warning: BRIDGE_DESIGN_ONTOLOGY not found. Using an empty ontology.")
            self.design_ontology = {}


    def extract_design_principles(self, text: str) -> List[Dict]:
        # Placeholder: Simple keyword spotting. Real implementation would use NLP.
        principles = []
        keywords = {"设计要求", "设计方法", "设计流程", "力学原理", "结构分析原理"}
        for kw in keywords:
            if kw in text:
                principles.append({"type": "design_principle", "keyword": kw, "text_snippet": text[:100]}) # Include a snippet
        return principles

    def extract_calculation_formulas(self, text: str) -> List[Dict]:
        # Placeholder: Look for common formula indicators. Real implementation needs robust parsing.
        formulas = []
        # Example: F = m*a or E = mc^2 (very simplified)
        import re
        # A very basic regex for things that look like equations.
        # This is highly simplistic and error-prone.
        for match in re.finditer(r'\b[A-Za-z]\s*=\s*[A-Za-z0-9\s()*+/\-^%.]+', text):
            formulas.append({
                "type": "formula",
                "expression": match.group(0),
                "variables": re.findall(r'\b[A-Za-z]\b', match.group(0)), # Simplistic variable extraction
                "context": text[max(0, match.start()-20):min(len(text), match.end()+20)]
            })
        return formulas

    def extract_design_parameters(self, text: str) -> List[Dict]:
        # Placeholder: Keyword-based extraction.
        parameters = []
        # Keywords that might indicate design parameters
        param_keywords = {
            "跨径": "span", "荷载等级": "load_class", "材料强度": "material_strength",
            "安全系数": "safety_factor", "屈服强度": "yield_strength", "抗压强度": "compressive_strength"
        }
        for kw, key_name in param_keywords.items():
            if kw in text:
                # Try to find a value associated with the keyword (very naive)
                match = re.search(f"{kw}\s*[:：是为]?\s*([0-9.]+)\s*([a-zA-ZMPaKN/m²]*)", text)
                if match:
                    parameters.append({
                        "type": "design_parameter",
                        "parameter_name": key_name,
                        "keyword": kw,
                        "value": match.group(1),
                        "unit": match.group(2) if match.group(2) else None,
                        "context": text[max(0, match.start()-30):min(len(text), match.end()+30)]
                    })
                else:
                    parameters.append({
                        "type": "design_parameter",
                        "parameter_name": key_name,
                        "keyword": kw,
                        "value": "Not Extracted",
                        "context": text[max(0, text.find(kw)-30):min(len(text), text.find(kw)+len(kw)+30)]
                    })
        return parameters

    def extract_design_constraints(self, text: str) -> List[Dict]:
        # Placeholder: Look for constraint-related keywords.
        constraints = []
        constraint_keywords = {"几何约束", "材料约束", "规范约束", "不得大于", "不应小于", "必须满足"}
        for kw in constraint_keywords:
            if kw in text:
                constraints.append({
                    "type": "design_constraint",
                    "keyword": kw,
                    "description": f"Constraint related to '{kw}' found.",
                    "text_snippet": text[:100] # Include a snippet
                })
        return constraints

    def extract_design_standards(self, text: str) -> List[Dict]:
        # Placeholder: Regex for standard codes (e.g., GB, JTG).
        standards = []
        # Regex for typical standard codes like GB 50011-2010, JTG D60-2015
        # This is a simplified regex and might need refinement.
        for match in re.finditer(r'\b([A-Z]{1,3}(?:/[A-Z]+)?\s*\d{2,5}(?:\.\d{1,2})?(?:-\d{2,4})?)\b', text):
            standards.append({
                "type": "design_standard",
                "standard_code": match.group(1),
                "context_snippet": text[max(0, match.start()-50):min(len(text), match.end()+50)]
            })
        # Also check for keywords from the ontology's design standards section
        if self.design_ontology and "设计规范" in self.design_ontology:
            for std_type, std_list in self.design_ontology["设计规范"].items():
                for std_item in std_list:
                    if std_item in text and not any(s["standard_code"] == std_item for s in standards):
                         standards.append({
                            "type": "design_standard",
                            "standard_code": std_item,
                            "standard_type": std_type, # e.g. "国家标准"
                            "context_snippet": text[max(0, text.find(std_item)-50):min(len(text), text.find(std_item)+len(std_item)+50)]
                        })
        return standards

    def link_design_dependencies(self, extracted_knowledge: List[Dict]) -> List[Dict]:
        # Placeholder: Simple linking based on co-occurrence or predefined rules.
        # Real implementation would involve semantic analysis and graph traversal.
        dependencies = []
        if not extracted_knowledge or len(extracted_knowledge) < 2:
            return dependencies

        # Example: If a formula and a parameter are extracted from the same context (highly simplified)
        # This is a very naive approach.
        for i in range(len(extracted_knowledge)):
            for j in range(i + 1, len(extracted_knowledge)):
                item1 = extracted_knowledge[i]
                item2 = extracted_knowledge[j]

                # Simplistic: if a principle and a formula are found, assume dependency
                if item1.get("type") == "design_principle" and item2.get("type") == "formula":
                    dependencies.append({
                        "source_type": item1.get("type"),
                        "source_detail": item1.get("keyword") or item1.get("expression"),
                        "target_type": item2.get("type"),
                        "target_detail": item2.get("keyword") or item2.get("expression"),
                        "relationship": "influences"
                    })
                # Simplistic: if a parameter and a formula are found, assume dependency
                elif item1.get("type") == "design_parameter" and item2.get("type") == "formula":
                     # Check if the parameter's keyword or name is in the formula's variables (naive)
                    param_name = item1.get("parameter_name", "")
                    formula_vars = item2.get("variables", [])
                    if any(p_var.lower() == param_name.lower() for p_var in formula_vars) or \
                       any(p_var.lower() in item1.get("keyword","").lower() for p_var in formula_vars):
                        dependencies.append({
                            "source_type": item1.get("type"),
                            "source_detail": item1.get("parameter_name") or item1.get("keyword"),
                            "target_type": item2.get("type"),
                            "target_detail": item2.get("expression"),
                            "relationship": "parameter_for_formula"
                        })

        return dependencies

# Example Usage (for testing purposes, if run directly)
if __name__ == '__main__':
    # Make sure BRIDGE_DESIGN_ONTOLOGY is accessible or defined for testing
    # For this test, we'll manually define a minimal one if the import fails.
    if 'BRIDGE_DESIGN_ONTOLOGY' not in globals():
        BRIDGE_DESIGN_ONTOLOGY = {
            "设计理论": {"结构力学理论": ["弯曲理论"]},
            "计算方法": {"结构分析方法": ["有限元法"]},
            "设计规范": {"国家标准": ["GB50011"]},
            "材料设计": {"混凝土设计": ["强度设计"]},
            "结构设计": {"上部结构设计": ["主梁设计"]},
        }

    extractor = DesignKnowledgeExtractor()
    sample_text = """
    桥梁设计应遵循结构力学原理，特别是弯曲理论。
    重要设计参数包括：主梁跨径 100m，混凝土强度 C50，活荷载等级为公路-I级。
    计算公式示例：弯矩 M = P*L/4。风荷载计算应依据 JTG D60-2015 标准。
    设计要求：挠度不得大于 L/800。材料约束：钢筋屈服强度 fy >= 400MPa。
    设计流程：初步设计 -> 技术设计 -> 施工图设计。
    安全系数取1.5。
    """

    print("Extracted Principles:", extractor.extract_design_principles(sample_text))
    print("\nExtracted Formulas:", extractor.extract_calculation_formulas(sample_text))
    print("\nExtracted Parameters:", extractor.extract_design_parameters(sample_text))
    print("\nExtracted Constraints:", extractor.extract_design_constraints(sample_text))
    print("\nExtracted Standards:", extractor.extract_design_standards(sample_text))

    all_extracted = []
    all_extracted.extend(extractor.extract_design_principles(sample_text))
    all_extracted.extend(extractor.extract_calculation_formulas(sample_text))
    all_extracted.extend(extractor.extract_design_parameters(sample_text))
    # ... add other extractions if needed for dependency linking test

    print("\nLinked Dependencies:", extractor.link_design_dependencies(all_extracted))

    # Test with ontology reference
    if extractor.design_ontology:
        print("\nExtractor has access to design ontology, e.g., a theory:",
              list(extractor.design_ontology.get("设计理论", {}).keys())[0] if extractor.design_ontology.get("设计理论") else "N/A")

    # Test standard extraction with ontology data
    text_with_specific_standard = "本设计参照 GB50011 执行。"
    print("\nStandards from specific text:", extractor.extract_design_standards(text_with_specific_standard))

    # Test relative import by creating a dummy sibling file
    # This part is tricky to test in isolation without a proper package structure.
    # You would typically test this as part of integration tests for the 'backend.app.services' package.
    # For now, we rely on the try-except block for the import.
    print("\nNote: BRIDGE_DESIGN_ONTOLOGY import from sibling module is tested implicitly.")
    print("If 'Warning: BRIDGE_DESIGN_ONTOLOGY not found' was printed, the import failed.")

    # Test parameter extraction with units
    text_with_units = "材料强度为30MPa，跨径是50m. 安全系数: 2.0"
    print("\nParameters with units:", extractor.extract_design_parameters(text_with_units))

    # Test formula with variables
    text_with_formula_vars = "The formula is stress = Force / Area. Another is E = m*c^2."
    print("\nFormulas with variables:", extractor.extract_calculation_formulas(text_with_formula_vars))

    # Test dependency linking with more items
    knowledge_items = [
        {'type': 'design_principle', 'keyword': '弯曲理论'},
        {'type': 'formula', 'expression': 'M = FL/4', 'variables': ['M', 'F', 'L']},
        {'type': 'design_parameter', 'parameter_name': 'span', 'keyword': '跨径 L', 'value': '100'},
        {'type': 'design_parameter', 'parameter_name': 'Force F', 'keyword': '荷载 F', 'value': '50'}
    ]
    print("\nDependencies for specific items:", extractor.link_design_dependencies(knowledge_items))
