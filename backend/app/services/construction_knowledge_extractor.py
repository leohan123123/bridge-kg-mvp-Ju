from typing import Dict, List
from backend.app.services.construction_ontology import CONSTRUCTION_ONTOLOGY

class ConstructionKnowledgeExtractor:
    def __init__(self):
        self.construction_ontology = CONSTRUCTION_ONTOLOGY
        # In a real application, you might load NLP models here
        # e.g., self.nlp = spacy.load("zh_core_web_sm")

    def _placeholder_extractor(self, text: str, category: str, keywords: List[str]) -> List[Dict]:
        """Helper function for placeholder extraction logic."""
        results = []
        # Simple keyword spotting. A real implementation would use NLP techniques.
        for keyword in keywords:
            if keyword in text:
                results.append({
                    "type": category,
                    "keyword_found": keyword,
                    "text_snippet": text[:100] + "..." if len(text) > 100 else text, # Basic snippet
                    "details": f"Details for {keyword} would be extracted here."
                })
        return results

    def extract_construction_processes(self, text: str) -> List[Dict]:
        """
        提取施工工艺流程
        识别：工序步骤、操作要点、技术要求
        Placeholder: Uses keywords from the ontology.
        """
        keywords = []
        for main_cat in self.construction_ontology.get("施工工艺流程", {}).values():
            keywords.extend(main_cat)

        extracted_processes = self._placeholder_extractor(text, "施工工艺流程", keywords)

        # Further refinement could involve identifying sequences, inputs/outputs, etc.
        # For example, looking for patterns like "首先...然后...最后..."
        # Or using dependency parsing to find relationships between actions and objects.

        # Example of adding more structure (very basic)
        if "基坑开挖" in text and "钻孔灌注桩" in text:
             extracted_processes.append({
                 "type": "工艺步骤",
                 "name": "基础施工初步序列",
                 "steps": ["基坑开挖", "钻孔灌注桩"],
                 "text_snippet": text[:100] + "..." if len(text) > 100 else text
             })
        return extracted_processes

    def extract_quality_standards(self, text: str) -> List[Dict]:
        """
        提取质量标准和控制要求
        识别：检验标准、验收要求、质量指标
        Placeholder: Uses keywords from the ontology.
        """
        keywords = []
        for main_cat in self.construction_ontology.get("施工技术标准", {}).values():
            keywords.extend(main_cat)
        for main_cat in self.construction_ontology.get("质量控制", {}).values():
            keywords.extend(main_cat)
        return self._placeholder_extractor(text, "质量标准", keywords)

    def extract_safety_requirements(self, text: str) -> List[Dict]:
        """
        提取安全要求和防护措施
        识别：安全规程、防护要求、应急措施
        Placeholder: Uses keywords from the ontology.
        """
        keywords = []
        for main_cat in self.construction_ontology.get("安全管理", {}).values():
            keywords.extend(main_cat)
        # Also check for safety standards
        keywords.extend(self.construction_ontology.get("施工技术标准", {}).get("安全标准", []))
        return self._placeholder_extractor(text, "安全要求", keywords)

    def extract_construction_parameters(self, text: str) -> List[Dict]:
        """
        提取施工参数
        如：配合比、养护条件、张拉控制值
        Placeholder: Looks for numerical values associated with keywords.
        """
        # This is a very naive placeholder. Real extraction needs regex, NLP for context.
        results = []
        param_keywords = ["配合比", "养护", "张拉", "温度", "湿度", "压力", "标高"]
        # Example: "混凝土配合比为1:2:3" or "养护温度20℃"
        # A real solution would use regular expressions and contextual analysis.
        for kw in param_keywords:
            if kw in text:
                # Attempt to find numbers or specific units near the keyword
                # This is highly simplified.
                import re
                # Try to find "keyword" followed by numbers/units, e.g., "温度 20 ℃" or "配合比 1:2:4"
                # This regex is very basic and for demonstration only.
                matches = re.finditer(rf"{kw}\s*[:：\s]*([\d\.:\/]+\s*[℃MPa%pH\w]*)", text)
                for match in matches:
                    results.append({
                        "type": "施工参数",
                        "parameter_name": kw,
                        "extracted_value": match.group(1).strip(),
                        "context": text[max(0, match.start()-20):min(len(text), match.end()+20)] # snippet
                    })
        if not results and any(kw in text for kw in param_keywords): # If keyword found but no value
            results.append({
                "type": "施工参数",
                "info": "Potential parameters mentioned, but specific values not extracted by this basic logic.",
                "text_snippet": text[:100] + "..." if len(text) > 100 else text
            })
        return results

    def extract_equipment_requirements(self, text: str) -> List[Dict]:
        """
        提取设备和工具要求
        识别：机械设备、工具器具、性能要求
        Placeholder: Uses keywords.
        """
        # Keywords could be expanded significantly
        keywords = ["挖掘机", "起重机", "泵车", "振捣器", "模板", "脚手架", "测量仪器"]
        return self._placeholder_extractor(text, "设备工具", keywords)

    def extract_material_specifications(self, text: str) -> List[Dict]:
        """
        提取材料规格和要求
        识别：材料性能、技术指标、验收标准
        Placeholder: Uses keywords.
        """
        keywords = ["水泥", "钢筋", "骨料", "外加剂", "防水材料", "涂料", "预应力筋"]
        # Could also look for patterns like "C30混凝土", "HRB400钢筋"
        results = self._placeholder_extractor(text, "材料规格", keywords)

        import re
        # Example for specific patterns like C30, HRB400
        material_patterns = {
            "混凝土强度等级": r"C\d{2,3}",
            "钢筋牌号": r"HRB\d{3,}|HPB\d{3,}"
        }
        for name, pattern in material_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                 results.append({
                    "type": "材料规格",
                    "specification_type": name,
                    "value": match.group(0),
                    "text_snippet": text[max(0, match.start()-20):min(len(text), match.end()+20)]
                })
        return results

    def link_process_dependencies(self, processes: List[Dict]) -> List[Dict]:
        """
        建立工艺流程间的依赖关系
        如：前置工序→当前工序→后续工序
        Placeholder: Assumes processes have 'id' and 'name', and tries to find simple keyword-based links.
        """
        # This is a very complex NLP task. Placeholder will be rudimentary.
        # A real implementation would use semantic understanding, temporal expressions, etc.

        # Example: If process A mentions "after completing X" and X is another process name.
        for i, current_process in enumerate(processes):
            current_process['predecessors'] = []
            current_process['successors'] = [] # Initialize

            # Simplified: check if process name appears in ontology under a known sequence
            # This is highly dependent on how processes are structured and named
            process_name = current_process.get("name", "").lower()

            # Check against CONSTRUCTION_ONTOLOGY structure (very basic)
            for category, sub_categories in self.construction_ontology.get("施工工艺流程", {}).items():
                for sub_category, process_list in sub_categories.items():
                    if process_name in [p.lower() for p in process_list]:
                        idx = [p.lower() for p in process_list].index(process_name)
                        if idx > 0:
                            # Assume the previous item in the list is a predecessor
                            # This is a strong assumption and likely needs more context
                            # Also, this assumes `processes` contains dicts with 'name' that match ontology
                            predecessor_name_in_ontology = process_list[idx-1].lower()
                            # Find this predecessor in the input `processes` list
                            for p in processes:
                                if p.get("name", "").lower() == predecessor_name_in_ontology:
                                    current_process['predecessors'].append(p.get('id', predecessor_name_in_ontology))
                                    # Also add successor link to the predecessor
                                    if 'successors' not in p: p['successors'] = []
                                    if current_process.get('id') not in p['successors']:
                                        p['successors'].append(current_process.get('id', current_process.get("name")))
                        break
                else:
                    continue
                break
        return processes
