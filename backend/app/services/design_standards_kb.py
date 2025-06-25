from typing import Dict, List, Any
import re

class DesignStandardsKB:
    def __init__(self):
        self.standards_database: Dict[str, Dict[str, Any]] = {} # Key: standard_code, Value: standard_data
        # Example standard_data:
        # {
        #   "code": "GB 50011-2010",
        #   "name": "建筑抗震设计规范",
        #   "version": "2010",
        #   "type": "国家标准", // e.g., 国家标准, 行业标准
        #   "clauses": [
        #       {"id": "1.0.1", "text": "为了...", "type": "强制性"},
        #       {"id": "3.2.1", "text": "...", "requirements": [...]}
        #   ],
        #   "formulas": [...],
        #   "tables": [...],
        #   "charts": [...]
        # }

    def parse_design_codes(self, code_documents: List[str]) -> Dict[str, Any]:
        """
        Parses a list of design code documents (text content).
        This is a placeholder. Real parsing would require sophisticated NLP and PDF/document processing.
        """
        parsed_count = 0
        errors = []
        for doc_content in code_documents:
            # Try to extract a standard code and a pseudo-name from the first few lines
            standard_code_match = re.search(r'\b([A-Z]{1,3}(?:/[A-Z]+)?\s*\d{2,5}(?:[.-]\d{2,4})?)\b', doc_content[:200])
            standard_name_match = re.search(r'《(.+?)》', doc_content[:200]) # Looking for a name like 《规范名称》

            if standard_code_match:
                code = standard_code_match.group(1).strip()
                name = standard_name_match.group(1) if standard_name_match else f"Unknown Standard {code}"

                if code in self.standards_database:
                    # Potentially update or skip if already exists
                    # For now, we'll skip if it exists to avoid overwriting with simplistic parsing
                    continue

                standard_data: Dict[str, Any] = {
                    "code": code,
                    "name": name,
                    "version": self._extract_version(code) or self._extract_version(doc_content[:200]),
                    "type": self._determine_standard_type(code),
                    "clauses": [], # Placeholder for actual clause extraction
                    "formulas": [], # Placeholder
                    "tables": [],   # Placeholder
                    "charts": [],   # Placeholder
                    "raw_text_snippet": doc_content[:500] # Store a snippet for now
                }

                # Mock clause extraction: find lines that look like clause IDs (e.g., "3.1.2 ...")
                for line_num, line in enumerate(doc_content.splitlines()):
                    clause_match = re.match(r'^\s*(\d{1,2}(?:\.\d{1,3}){1,3})\s+(.+)', line)
                    if clause_match:
                        clause_id = clause_match.group(1)
                        clause_text = clause_match.group(2)
                        clause_type = "推荐性" # Default
                        if "强制性条文" in line or "必须" in clause_text or "应" == clause_text.strip().split()[0]:
                             clause_type = "强制性"

                        standard_data["clauses"].append({
                            "id": clause_id,
                            "text": clause_text,
                            "type": clause_type, # "强制性" or "推荐性"
                            "page_reference": line_num + 1 # Mock page reference
                        })

                self.standards_database[code] = standard_data
                parsed_count += 1
            else:
                errors.append(f"Could not identify standard code in document starting with: {doc_content[:100]}...")

        return {"parsed_count": parsed_count, "total_documents": len(code_documents), "errors": errors}

    def _extract_version(self, text: str) -> str:
        # Simple version extraction (e.g., from "GB 50011-2010" or "JTG D60-2015")
        match = re.search(r'-(20\d{2}|19\d{2})\b', text)
        return match.group(1) if match else ""

    def _determine_standard_type(self, code: str) -> str:
        if code.startswith("GB"): return "国家标准"
        if code.startswith("JTG") or code.startswith("JTJ"): return "行业标准 (交通)"
        if code.startswith("TB"): return "行业标准 (铁路)"
        if code.startswith("DB"): return "地方标准"
        # ... add more rules for other standard types
        return "未知类型"

    def build_standards_hierarchy(self, standards_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds a hierarchy from a list of standard objects (e.g., from parsed data).
        This method assumes standards_list contains objects like those in self.standards_database.
        The hierarchy is conceptual and based on type (国标 > 行标 > 地标).
        """
        hierarchy: Dict[str, Dict[str, List[Any]]] = {
            "国家标准": {"items": []},
            "行业标准": {"items": []},
            "地方标准": {"items": []},
            "企业标准": {"items": []}, # Assuming '企标' means 企业标准 (Enterprise Standard)
            "国际标准": {"items": []}, # Added from ontology
            "未知类型": {"items": []}
        }

        # Use standards from database if standards_list is empty, otherwise use provided list
        source_standards = standards_list if standards_list else self.standards_database.values()

        for std in source_standards:
            std_type = std.get("type", "未知类型")
            if std_type in hierarchy:
                hierarchy[std_type]["items"].append(std)
            else: # If a new type appears
                hierarchy[std_type] = {"items": [std]}

        return hierarchy

    def extract_design_requirements(self, standard_code: str, clause_id: str = None) -> List[Dict[str, Any]]:
        """
        Extracts design requirements from a specific standard or clause.
        """
        requirements = []
        standard = self.standards_database.get(standard_code)
        if not standard:
            return [{"error": f"Standard {standard_code} not found."}]

        clauses_to_check = standard.get("clauses", [])
        if clause_id:
            clauses_to_check = [c for c in clauses_to_check if c.get("id") == clause_id]
            if not clauses_to_check:
                 return [{"error": f"Clause {clause_id} not found in standard {standard_code}."}]

        for clause in clauses_to_check:
            # Simple requirement extraction: look for keywords
            # This is highly dependent on the clause text structure.
            text = clause.get("text", "")
            req_type = clause.get("type", "推荐性") # e.g. "强制性", "推荐性"

            # Example keywords indicating a requirement
            if "应" in text or "必须" in text or "不得" in text or "不应" in text or "宜" in text:
                requirements.append({
                    "standard_code": standard_code,
                    "clause_id": clause.get("id"),
                    "requirement_text": text,
                    "type": req_type, # "强制性", "推荐性"
                    # Further NLP could extract specific constraints, values, conditions
                    "details": "Extracted based on keywords."
                })
        return requirements

    def create_compliance_rules(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Creates compliance check rules from extracted requirements.
        This is a placeholder. Real rule generation would be complex.
        Rule format could be: {"condition": "parameter X > Y", "source_standard": "GB Z", "clause": "A.B.C"}
        """
        rules = []
        for req in requirements:
            if req.get("error"): continue # Skip error entries

            # Simplistic rule generation (example)
            # If a requirement text contains "不得大于 X" (must not be greater than X)
            # and X is a number.
            text = req.get("requirement_text", "")
            match_max = re.search(r'(不得大于|不应大于|不宜大于)\s*([0-9.]+)([a-zA-Z%/\w²]*)', text)
            match_min = re.search(r'(不得小于|不应小于|不宜小于)\s*([0-9.]+)([a-zA-Z%/\w²]*)', text)
            match_equal = re.search(r'(应等于|应为)\s*([0-9.]+)([a-zA-Z%/\w²]*)', text) # More specific, less common

            rule = {
                "standard_code": req.get("standard_code"),
                "clause_id": req.get("clause_id"),
                "requirement_text": text,
                "rule_description": "N/A"
            }

            if match_max:
                rule["rule_description"] = f"Value must be <= {match_max.group(2)} {match_max.group(3)}."
                rule["condition_type"] = "max_value"
                rule["value"] = float(match_max.group(2))
                rule["unit"] = match_max.group(3) if match_max.group(3) else None
                rules.append(rule)
            elif match_min:
                rule["rule_description"] = f"Value must be >= {match_min.group(2)} {match_min.group(3)}."
                rule["condition_type"] = "min_value"
                rule["value"] = float(match_min.group(2))
                rule["unit"] = match_min.group(3) if match_min.group(3) else None
                rules.append(rule)
            elif match_equal: # Less common to be purely numeric
                rule["rule_description"] = f"Value must be == {match_equal.group(2)} {match_equal.group(3)}."
                rule["condition_type"] = "exact_value"
                rule["value"] = float(match_equal.group(2))
                rule["unit"] = match_equal.group(3) if match_equal.group(3) else None
                rules.append(rule)
            elif req.get("type") == "强制性": # Generic rule for mandatory clauses if no specific value found
                rule["rule_description"] = f"Mandatory clause: must be complied with. Details: '{text[:50]}...'"
                rule["condition_type"] = "mandatory_compliance"
                rules.append(rule)

        return rules

    def update_standards_version(self, old_standard_code: str, new_standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates a standard to a new version or adds a new standard.
        `new_standard_data` should be a dictionary similar to how standards are stored.
        """
        new_code = new_standard_data.get("code")
        if not new_code:
            return {"success": False, "message": "New standard data must include a 'code'."}

        if old_standard_code in self.standards_database:
            # If we are truly "updating" an existing one by replacing it.
            # Or, if new_code is different, it's more like adding new and potentially archiving old.
            # For simplicity, we'll remove old and add new if codes are different.
            # If codes are same, it's a direct update.
            if old_standard_code != new_code:
                del self.standards_database[old_standard_code]

            self.standards_database[new_code] = new_standard_data
            return {"success": True, "message": f"Standard {old_standard_code} updated/replaced with {new_code}."}
        else:
            # If old_standard_code doesn't exist, this is effectively adding the new standard.
            self.standards_database[new_code] = new_standard_data
            return {"success": True, "message": f"New standard {new_code} added."}

    def get_standard(self, standard_code: str) -> Dict[str, Any] | None:
        return self.standards_database.get(standard_code)

# Example Usage (for testing purposes)
if __name__ == '__main__':
    kb = DesignStandardsKB()

    # 1. Parse design codes
    doc1_content = """
    《建筑抗震设计规范》 GB 50011-2010
    1.0.1 为了在建筑抗震设计中贯彻执行国家有关防震减灾的方针政策... (强制性条文)
    3.1.1 建筑结构应根据其使用功能的重要性分为甲、乙、丙、丁类。
    3.2.1 钢筋的抗拉强度不应小于300MPa。混凝土强度等级不得低于C20。
    A.1.1 附录A条文。
    """
    doc2_content = """
    公路桥涵设计通用规范 JTG D60-2015
    1.0.5 设计使用年限：特大桥、大桥、中桥应为100年。 (强制性条文)
    4.1.2 车辆荷载计算应考虑冲击系数。最大挠度不得大于 L/500。
    """
    parsing_result = kb.parse_design_codes([doc1_content, doc2_content])
    print("Parsing Result:", parsing_result)
    print("Standards in DB after parsing:", list(kb.standards_database.keys()))
    # print("GB 50011-2010 clauses:", kb.standards_database.get("GB 50011-2010", {}).get("clauses"))


    # 2. Build standards hierarchy
    hierarchy = kb.build_standards_hierarchy([]) # Pass empty to use internal DB
    print("\nStandards Hierarchy:")
    for std_type, data in hierarchy.items():
        if data["items"]:
            print(f"  {std_type}: {[std['code'] for std in data['items']]}")

    # 3. Extract design requirements
    gb_requirements = kb.extract_design_requirements("GB 50011-2010")
    print("\nRequirements from GB 50011-2010:", gb_requirements)

    jtg_clause_req = kb.extract_design_requirements("JTG D60-2015", "4.1.2")
    print("\nRequirements from JTG D60-2015 (Clause 4.1.2):", jtg_clause_req)


    # 4. Create compliance rules
    gb_rules = kb.create_compliance_rules(gb_requirements)
    print("\nCompliance Rules from GB 50011-2010 requirements:", gb_rules)

    jtg_rules_from_reqs = kb.create_compliance_rules(jtg_clause_req)
    print("\nCompliance Rules from JTG D60-2015 (Clause 4.1.2) requirements:", jtg_rules_from_reqs)


    # 5. Update standards version
    new_gb_data = {
        "code": "GB 50011-2018", # New version
        "name": "建筑抗震设计规范 (新版)",
        "version": "2018",
        "type": "国家标准",
        "clauses": [{"id": "1.0.1", "text": "新版总则...", "type": "强制性"}],
        "raw_text_snippet": "新版内容..."
    }
    update_result = kb.update_standards_version("GB 50011-2010", new_gb_data)
    print("\nUpdate Result:", update_result)
    print("Standards in DB after update:", list(kb.standards_database.keys()))
    print("New GB 50011-2018 data:", kb.get_standard("GB 50011-2018"))

    # Test adding a completely new standard via update method
    new_dbj_data = {
        "code": "DBJ/T 15-82-2023",
        "name": "地方建筑标准示例",
        "version": "2023",
        "type": "地方标准",
        "clauses": [{"id": "1.1", "text": "地方标准内容...", "type": "推荐性"}],
    }
    add_result = kb.update_standards_version("DBJ_OLD_CODE_NONEXISTENT", new_dbj_data) # old code doesn't exist
    print("\nAdd New Standard Result:", add_result)
    print("Standards in DB after adding DBJ:", list(kb.standards_database.keys()))
    print("DBJ Data:", kb.get_standard("DBJ/T 15-82-2023"))

    # Test error case for requirement extraction
    error_req = kb.extract_design_requirements("NON_EXISTENT_CODE")
    print("\nRequirements from NON_EXISTENT_CODE:", error_req)
    error_req_clause = kb.extract_design_requirements("JTG D60-2015", "9.9.9") # Non-existent clause
    print("\nRequirements from JTG D60-2015 (Clause 9.9.9):", error_req_clause)
