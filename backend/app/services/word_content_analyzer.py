from typing import Dict, List, Any
from app.services.bridge_entity_extractor import BridgeEntityExtractor
import logging

logger = logging.getLogger(__name__)

class WordContentAnalyzer:
    def __init__(self):
        """
        Initializes the WordContentAnalyzer.
        It uses BridgeEntityExtractor for specialized entity extraction.
        """
        try:
            # Assuming BridgeEntityExtractor is available and can be instantiated.
            # If it requires configuration or has dependencies, that needs to be handled.
            self.bridge_extractor = BridgeEntityExtractor()
        except Exception as e:
            logger.error(f"Failed to initialize BridgeEntityExtractor in WordContentAnalyzer: {e}")
            # Depending on the application's needs, either raise the exception
            # or set self.bridge_extractor to None and handle it in methods.
            # For now, let it raise to make the problem visible immediately.
            raise

    def analyze_technical_standard(self, parsed_content: Dict) -> Dict:
        """
        Analyzes content parsed from a technical standard document.
        Aims to identify:条文 (clauses/articles), 技术要求 (technical requirements),
        参数指标 (parameter indicators), etc.

        Args:
            parsed_content (Dict): The output from WordParserService.extract_text_content,
                                   expected to have at least a "text" field.

        Returns:
            Dict: Analysis results, which might include extracted entities categorized
                  by their relevance to technical standards.
        """
        logger.info("Analyzing content as a Technical Standard.")
        text_content = parsed_content.get("text")
        if not text_content:
            logger.warning("No text content provided for technical standard analysis.")
            return {"analysis_type": "technical_standard", "status": "error", "message": "No text content"}

        # Use BridgeEntityExtractor to find relevant entities.
        # The definition of "条文", "技术要求", "参数指标" needs to be mapped to
        # the capabilities of BridgeEntityExtractor.
        # This might involve looking for specific keywords, patterns, or entity types
        # that the extractor is trained or programmed to identify.

        # Example: Extract all professional entities and then try to categorize them further
        # or look for patterns indicative of "条文" (e.g., numbered paragraphs with specific keywords).
        extracted_entities = self.bridge_extractor.extract_professional_entities(text_content)

        # Placeholder for more specific analysis logic for technical standards.
        # For example, one might search for patterns like "第 X 条", "应符合", "不应小于", etc.
        # and associate them with nearby entities.

        identified_clauses = [] # List of identified clauses/articles
        technical_requirements = [] # List of identified technical requirements
        parameter_indicators = [] # List of identified parameter indicators

        # This is a simplified approach. Real analysis would be more complex.
        # For MVP, we can rely on the general entity extraction and perhaps flag certain
        # categories of entities as being particularly relevant to standards.
        # For example, if BridgeEntityExtractor identifies "材料强度" as a "性能参数",
        # that could be a "parameter indicator".

        # This is a placeholder for actual analysis logic.
        # For now, we'll just return the raw entities grouped by category from bridge_extractor.
        # A more sophisticated implementation would involve rule-based systems or ML models
        # to specifically identify "条文", "技术要求", etc.

        analysis_results = {
            "analysis_type": "technical_standard",
            "extracted_entities_by_category": extracted_entities,
            # "identified_clauses": identified_clauses, # Future enhancement
            # "technical_requirements": technical_requirements, # Future enhancement
            # "parameter_indicators": parameter_indicators # Future enhancement
            "status": "success"
        }
        logger.info(f"Technical standard analysis completed. Found {len(extracted_entities)} entity categories.")
        return analysis_results

    def analyze_design_specification(self, parsed_content: Dict) -> Dict:
        """
        Analyzes content parsed from a design specification document.
        Aims to identify: 设计方法 (design methods), 计算公式 (calculation formulas),
        设计参数 (design parameters), etc.

        Args:
            parsed_content (Dict): The output from WordParserService.extract_text_content.

        Returns:
            Dict: Analysis results.
        """
        logger.info("Analyzing content as a Design Specification.")
        text_content = parsed_content.get("text")
        if not text_content:
            logger.warning("No text content provided for design specification analysis.")
            return {"analysis_type": "design_specification", "status": "error", "message": "No text content"}

        extracted_entities = self.bridge_extractor.extract_professional_entities(text_content)

        # Placeholder for specific logic for design specifications.
        # e.g., regex for formulas, keywords for design methods.
        # If BridgeEntityExtractor can identify "设计参数" (Design Parameter) entities, they would be key here.

        analysis_results = {
            "analysis_type": "design_specification",
            "extracted_entities_by_category": extracted_entities,
            "status": "success"
        }
        logger.info(f"Design specification analysis completed. Found {len(extracted_entities)} entity categories.")
        return analysis_results

    def analyze_construction_manual(self, parsed_content: Dict) -> Dict:
        """
        Analyzes content parsed from a construction manual.
        Aims to identify: 工艺流程 (process flows), 质量标准 (quality standards),
        操作规程 (operating procedures), etc.

        Args:
            parsed_content (Dict): The output from WordParserService.extract_text_content.

        Returns:
            Dict: Analysis results.
        """
        logger.info("Analyzing content as a Construction Manual.")
        text_content = parsed_content.get("text")
        if not text_content:
            logger.warning("No text content provided for construction manual analysis.")
            return {"analysis_type": "construction_manual", "status": "error", "message": "No text content"}

        extracted_entities = self.bridge_extractor.extract_professional_entities(text_content)

        # Placeholder for specific logic for construction manuals.
        # e.g., keywords for "工艺", "质量", "操作".

        analysis_results = {
            "analysis_type": "construction_manual",
            "extracted_entities_by_category": extracted_entities,
            "status": "success"
        }
        logger.info(f"Construction manual analysis completed. Found {len(extracted_entities)} entity categories.")
        return analysis_results

    def extract_technical_parameters(self, tables: List[Dict]) -> Dict:
        """
        Extracts technical parameters from tables.
        Example parameters: 材料强度 (material strength), 尺寸规格 (dimensional specifications),
        荷载标准 (load standards), etc.

        Args:
            tables (List[Dict]): A list of tables, where each table is as returned by
                                 WordParserService.extract_tables (e.g., a list of rows,
                                 where each row is a list of cell strings).

        Returns:
            Dict: A dictionary containing extracted parameters, possibly organized by table
                  or by parameter type. Structure TBD based on requirements.
                  For MVP, could be a list of identified {parameter_name: value, unit: unit, source_table_index: index}
        """
        logger.info(f"Extracting technical parameters from {len(tables)} tables.")
        if not tables:
            return {"status": "no_tables_provided", "extracted_parameters": []}

        all_extracted_parameters = []

        for table_info in tables:
            table_data = table_info.get("data", []) # List of rows
            table_index = table_info.get("table_index", "N/A")

            # The logic here is highly dependent on table structures and the nature of parameters.
            # This requires heuristics or ML models for robust extraction.
            # For an MVP, we might:
            # 1. Look for keywords in table headers or the first column.
            # 2. Assume a simple key-value structure in rows (e.g., Col1=ParameterName, Col2=Value).
            # 3. Use BridgeEntityExtractor on cell text to identify known parameter types.

            # Simplified example: iterate through cells and use bridge_extractor on cell text.
            # This is very naive and likely to be noisy without further refinement.
            current_table_params = []
            for r_idx, row in enumerate(table_data):
                for c_idx, cell_text in enumerate(row):
                    if not cell_text.strip():
                        continue

                    # Use bridge_extractor to see if cell_text contains known entities/parameters
                    # This is a proxy for actual parameter extraction.
                    # extract_professional_entities returns a dict like:
                    # {'Category1': [{'term': 'TermA', ...}, ...], 'Category2': [...]}
                    cell_entities_by_cat = self.bridge_extractor.extract_professional_entities(cell_text)

                    for category, entities_list in cell_entities_by_cat.items():
                        for entity_info in entities_list:
                            # We need a way to determine if this entity is a "parameter".
                            # This depends on the ontology used by BridgeEntityExtractor.
                            # Let's assume some categories are explicitly parameters, e.g., "性能参数", "设计参数".
                            # Or, we can have a predefined list of parameter keywords.
                            # For this example, let's say if an entity is extracted, we consider it a potential parameter.
                            # This is a placeholder for more intelligent identification.
                            current_table_params.append({
                                "term": entity_info["term"],
                                "category": category,
                                "sub_category": entity_info.get("sub_category"),
                                "source_table_index": table_index,
                                "row": r_idx,
                                "column": c_idx,
                                "cell_context": cell_text[:100] # snippet of cell text
                            })

            if current_table_params:
                all_extracted_parameters.extend(current_table_params)
                logger.info(f"Found {len(current_table_params)} potential parameter mentions in table {table_index}.")

        logger.info(f"Completed technical parameter extraction from tables. Found {len(all_extracted_parameters)} total potential parameter mentions.")
        return {
            "status": "success",
            "extracted_parameters_summary": all_extracted_parameters # This will be a list of dicts.
        }

# Example of how to use (illustrative)
if __name__ == '__main__':
    # This section needs the BridgeEntityExtractor to be functional and configured.
    # And sample data (parsed_content, tables).

    # Mock BridgeEntityExtractor if needed for isolated testing of WordContentAnalyzer logic
    class MockBridgeEntityExtractor:
        def extract_professional_entities(self, text: str) -> Dict[str, List[Dict[str, str]]]:
            # Simulate extraction
            if "强度" in text: # Strength
                return {"性能参数": [{"term": "混凝土强度C30", "sub_category": "材料强度", "category": "性能参数"}]}
            if "设计荷载" in text: # Design Load
                return {"设计参数": [{"term": "设计荷载50kN/m2", "sub_category": "荷载标准", "category": "设计参数"}]}
            return {}

    # Replace the actual extractor with the mock for this example run
    # In a real scenario, WordContentAnalyzer would use the actual BridgeEntityExtractor
    original_extractor = BridgeEntityExtractor
    BridgeEntityExtractor = MockBridgeEntityExtractor

    analyzer = WordContentAnalyzer()

    # Restore original BridgeEntityExtractor if other tests in this file need it
    BridgeEntityExtractor = original_extractor

    # 1. Test analyze_technical_standard
    sample_parsed_content_standard = {
        "text": "本文档规定了桥梁设计的基本原则。混凝土强度C30是重要指标。设计荷载应符合规范。",
        "structure": [], "metadata": {}
    }
    analysis_std = analyzer.analyze_technical_standard(sample_parsed_content_standard)
    print("--- Technical Standard Analysis ---")
    # print(analysis_std)
    if analysis_std.get("extracted_entities_by_category"):
        print(f"Entities for standard: {analysis_std['extracted_entities_by_category']}")


    # 2. Test analyze_design_specification
    sample_parsed_content_spec = {
        "text": "设计规范要求计算挠度。设计荷载50kN/m2。",
        "structure": [], "metadata": {}
    }
    analysis_spec = analyzer.analyze_design_specification(sample_parsed_content_spec)
    print("\n--- Design Specification Analysis ---")
    # print(analysis_spec)
    if analysis_spec.get("extracted_entities_by_category"):
        print(f"Entities for spec: {analysis_spec['extracted_entities_by_category']}")

    # 3. Test analyze_construction_manual (similar structure)
    # ...

    # 4. Test extract_technical_parameters
    sample_tables_data = [
        {
            "table_index": 0,
            "data": [
                ["参数名称", "数值", "单位"],
                ["混凝土强度C30", "30", "MPa"],
                ["钢筋屈服强度", "400", "MPa"]
            ]
        },
        {
            "table_index": 1,
            "data": [
                ["荷载类型", "标准值"],
                ["设计荷载50kN/m2", "50 kN/m2"]
            ]
        }
    ]
    parameters_from_tables = analyzer.extract_technical_parameters(sample_tables_data)
    print("\n--- Technical Parameters from Tables ---")
    # print(parameters_from_tables)
    if parameters_from_tables.get("extracted_parameters_summary"):
        for param_info in parameters_from_tables["extracted_parameters_summary"]:
            print(f"  Param: {param_info['term']} (Cat: {param_info['category']}) from table {param_info['source_table_index']}")

    # Remember to re-enable BridgeEntityExtractor if it was mocked for testing purposes
    # BridgeEntityExtractor = original_bridge_extractor_class

    pass
