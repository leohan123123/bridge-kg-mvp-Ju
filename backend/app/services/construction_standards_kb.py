from typing import Dict, List

class ConstructionStandardsKB:
    def __init__(self):
        self.standards_database = {} # Stores parsed specification documents
        self.quality_standards = {} # Stores quality control matrices or related data
        # Example: self.nlp = spacy.load("zh_core_web_sm") for text processing

    def parse_construction_specifications(self, spec_documents: List[str]) -> Dict:
        """
        解析施工技术规范 (e.g., JTG, GB standards).
        提取：技术要求、工艺标准、验收标准.
        This is a placeholder. Real parsing requires sophisticated NLP and understanding of document structures.
        Input `spec_documents` could be file paths or raw text content.
        """
        parsed_data = {"specifications": [], "errors": []}

        for i, doc_content in enumerate(spec_documents):
            # In a real scenario, doc_content might be a path to a PDF/DOCX file,
            # requiring libraries like pdfplumber, python-docx, etc.
            # For this placeholder, assume doc_content is a string.

            # Placeholder logic: Simple keyword search
            # A real system would use NLP to identify sections, clauses, tables, etc.
            # and extract structured information.

            # Example keywords to identify different types of information
            tech_keywords = ["技术要求", "设计规定", "施工要求"]
            process_keywords = ["工艺流程", "施工方法", "作业指导"]
            acceptance_keywords = ["验收标准", "检验批", "质量标准", "合格标准"]

            extracted_spec = {
                "doc_id": f"doc_{i+1}",
                "content_snippet": doc_content[:200] + "..." if len(doc_content) > 200 else doc_content,
                "technical_requirements": [],
                "process_standards": [],
                "acceptance_criteria": []
            }

            # Very basic search for keywords
            if any(kw in doc_content for kw in tech_keywords):
                extracted_spec["technical_requirements"].append("Placeholder: Found technical requirement indicators.")
            if any(kw in doc_content for kw in process_keywords):
                extracted_spec["process_standards"].append("Placeholder: Found process standard indicators.")
            if any(kw in doc_content for kw in acceptance_keywords):
                extracted_spec["acceptance_criteria"].append("Placeholder: Found acceptance criteria indicators.")

            if not extracted_spec["technical_requirements"] and \
               not extracted_spec["process_standards"] and \
               not extracted_spec["acceptance_criteria"]:
                extracted_spec["info"] = "No specific keywords found by basic parser."

            parsed_data["specifications"].append(extracted_spec)
            self.standards_database[extracted_spec["doc_id"]] = extracted_spec

        return parsed_data

    def build_quality_control_matrix(self, quality_docs: List[str]) -> Dict:
        """
        构建质量控制矩阵: 工序→控制点→检验方法→验收标准.
        `quality_docs` could be text from relevant sections of specs or specific quality plans.
        Placeholder implementation.
        """
        # matrix_schema = {
        #     "process_name": {
        #         "control_point_id": {
        #             "description": "e.g., Rebar spacing",
        #             "inspection_method": "e.g., Visual, Tape measure",
        #             "acceptance_standard_ref": "e.g., GB50204 Clause 5.2.1",
        #             "standard_value": "e.g., Spacing 100mm +/- 5mm"
        #         }
        #     }
        # }
        # This would typically be built by extracting structured data from `quality_docs`
        # or by linking to parsed specifications from `self.standards_database`.

        control_matrix = {}
        for i, doc_text in enumerate(quality_docs):
            # Placeholder: Assume `doc_text` describes one or more control points.
            # A real implementation would parse this text to populate the matrix.
            # Example: "对于钢筋绑扎工序，检查钢筋间距，使用卷尺测量，符合JTG F50表3.3.2要求。"

            # Rudimentary keyword-based extraction for demonstration
            process_name = f"UnknownProcess_Doc{i}"
            control_point_desc = "Generic Control Point"
            inspection_method = "Visual/Measurement (Placeholder)"
            acceptance_standard = "Relevant Standard (Placeholder)"

            if "钢筋" in doc_text and "间距" in doc_text:
                process_name = "钢筋施工"
                control_point_desc = "钢筋间距检查"
                if "卷尺" in doc_text: inspection_method = "卷尺测量"
                if "JTG" in doc_text or "GB" in doc_text: acceptance_standard = "Relevant JTG/GB standard mentioned"

            if process_name not in control_matrix:
                control_matrix[process_name] = []

            control_matrix[process_name].append({
                "control_point_id": f"CP_{i}_{len(control_matrix[process_name])}",
                "description": control_point_desc,
                "inspection_method": inspection_method,
                "acceptance_standard_ref": acceptance_standard,
                "source_doc_snippet": doc_text[:150] + "..." if len(doc_text) > 150 else doc_text
            })

        self.quality_standards = control_matrix # Store the built matrix
        return control_matrix

    def extract_safety_protocols(self, safety_docs: List[str]) -> List[Dict]:
        """
        提取安全操作规程.
        识别：安全要求、防护措施、应急程序.
        Placeholder.
        """
        protocols = []
        for i, doc_text in enumerate(safety_docs):
            # Placeholder logic. Real extraction would involve NLP to identify specific
            # safety instructions, PPE requirements, emergency contacts, etc.
            protocol = {
                "doc_id": f"safety_doc_{i}",
                "title": f"Safety Protocol from Doc {i} (Placeholder)",
                "safety_requirements": [],
                "protective_measures": [],
                "emergency_procedures": [],
                "source_snippet": doc_text[:150] + "..." if len(doc_text) > 150 else doc_text
            }
            if "安全帽" in doc_text or "安全带" in doc_text:
                protocol["protective_measures"].append("PPE Mentioned (e.g., helmet, harness)")
            if "高空作业" in doc_text:
                protocol["safety_requirements"].append("High-altitude work precautions likely mentioned.")
            if "应急" in doc_text or "事故处理" in doc_text:
                protocol["emergency_procedures"].append("Emergency response information likely present.")

            if not protocol["safety_requirements"] and not protocol["protective_measures"] and not protocol["emergency_procedures"]:
                 protocol["info"] = "Generic safety document - specific items not extracted by basic parser."

            protocols.append(protocol)
        return protocols

    def create_inspection_checklists(self, standards: List[Dict]) -> List[Dict]:
        """
        创建检查清单.
        基于标准生成施工检查和验收清单.
        `standards` could be data from `parse_construction_specifications` or `build_quality_control_matrix`.
        Placeholder.
        """
        checklists = []
        # This function would iterate through structured standard data (e.g., quality control points)
        # and format them into actionable checklist items.

        # Example: if `standards` is a list of control points from the quality matrix
        # (assuming `standards` is what `build_quality_control_matrix` might return, or a part of it)

        # For this placeholder, let's assume `standards` is a list of dicts,
        # where each dict has 'description', 'inspection_method', 'acceptance_standard_ref'.

        for i, std_item in enumerate(standards):
            # std_item could be a control point from the quality matrix
            if isinstance(std_item, dict) and "description" in std_item and "acceptance_standard_ref" in std_item:
                checklist_item = {
                    "item_id": f"chk_{i+1}",
                    "task_description": std_item.get("description", "N/A"),
                    "inspection_method": std_item.get("inspection_method", "N/A"),
                    "standard_reference": std_item.get("acceptance_standard_ref", "N/A"),
                    "verification_status": "Pending", # Could be Pending, Pass, Fail, N/A
                    "notes": ""
                }
                checklists.append(checklist_item)
            else:
                # Fallback for less structured input
                 checklists.append({
                    "item_id": f"chk_generic_{i+1}",
                    "task_description": f"Review standard item: {str(std_item)[:50]}...",
                    "standard_reference": "Refer to source document",
                    "verification_status": "Pending",
                    "notes": "Input standard format was not fully structured for detailed checklist generation."
                 })
        return checklists

    def track_standard_compliance(self, construction_data: Dict, standards: List[Dict]) -> Dict:
        """
        跟踪标准符合性.
        检查施工过程数据 (`construction_data`) 是否符合相关标准 (`standards`).
        `construction_data` could be field reports, sensor data, test results.
        `standards` could be parsed criteria or checklists.
        Placeholder.
        """
        # This is a complex function that would involve:
        # 1. Mapping `construction_data` items to relevant `standards`.
        # 2. Comparing reported values/observations against standard requirements.
        # 3. Flagging deviations or non-compliance.

        compliance_report = {
            "summary": "Compliance check placeholder.",
            "compliant_items": 0,
            "non_compliant_items": 0,
            "details": []
        }

        # Example: Assume construction_data has {'parameter_name': 'concrete_strength_test', 'value': '35MPa'}
        # And standards has [{'item_id': 'std_concrete', 'parameter_name': 'concrete_strength', 'min_value': '30MPa'}]

        # This is a very simplified check
        num_standards_checked = 0
        if isinstance(construction_data, dict) and isinstance(standards, list):
            for std_item in standards:
                if isinstance(std_item, dict) and "parameter_name" in std_item and "min_value" in std_item:
                    param_name = std_item["parameter_name"]
                    min_value_str = std_item["min_value"] # e.g., "30MPa"

                    # Naive value extraction and comparison
                    try:
                        # Attempt to extract numeric part and unit for standard
                        std_val_numeric = float("".join(filter(str.isdigit or str.isspace or str.isdecimal, min_value_str.split("MPa")[0])))

                        if param_name in construction_data and "value" in construction_data[param_name]:
                            actual_value_str = construction_data[param_name]["value"] # e.g., "35MPa"
                            actual_val_numeric = float("".join(filter(str.isdigit or str.isspace or str.isdecimal, actual_value_str.split("MPa")[0])))

                            num_standards_checked +=1
                            if actual_val_numeric >= std_val_numeric:
                                compliance_report["compliant_items"] += 1
                                compliance_report["details"].append({
                                    "standard_id": std_item.get("item_id", "UnknownStd"),
                                    "parameter": param_name,
                                    "status": "Compliant",
                                    "reported_value": actual_value_str,
                                    "required_value": min_value_str
                                })
                            else:
                                compliance_report["non_compliant_items"] += 1
                                compliance_report["details"].append({
                                    "standard_id": std_item.get("item_id", "UnknownStd"),
                                    "parameter": param_name,
                                    "status": "Non-Compliant",
                                    "reported_value": actual_value_str,
                                    "required_value": min_value_str,
                                    "deviation": f"{actual_val_numeric - std_val_numeric}"
                                })
                    except ValueError:
                        # Could not parse values for comparison
                        compliance_report["details"].append({
                            "standard_id": std_item.get("item_id", "UnknownStd"),
                            "parameter": param_name,
                            "status": "Error",
                            "message": "Could not parse values for comparison."
                        })

        if num_standards_checked == 0:
             compliance_report["summary"] = "Compliance check placeholder. No specific comparable items found or processed."
        else:
             compliance_report["summary"] = f"Compliance check complete. Checked {num_standards_checked} items."

        return compliance_report
