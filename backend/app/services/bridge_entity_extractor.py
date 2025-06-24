from typing import Dict, List, Tuple
import re

BRIDGE_ENGINEERING_ONTOLOGY = {
    "结构类型": {
        "桥梁类型": ["悬索桥", "斜拉桥", "梁桥", "拱桥", "刚构桥", "桁架桥", "组合桥"],
        "上部结构": ["主梁", "横梁", "桥面板", "栏杆", "伸缩缝"],
        "下部结构": ["桥墩", "桥台", "基础", "承台", "桩基"],
        "附属结构": ["支座", "防撞护栏", "排水系统", "照明系统"]
    },
    "材料类型": {
        "主要材料": ["钢材", "混凝土", "预应力钢绞线", "钢筋", "沥青"],
        "钢材类型": ["碳钢", "合金钢", "不锈钢", "耐候钢"],
        "混凝土类型": ["普通混凝土", "高强混凝土", "预应力混凝土", "纤维混凝土"]
    },
    "技术规范": {
        "设计规范": ["公路桥涵设计通用规范", "城市桥梁设计规范", "铁路桥涵设计规范"],
        "施工规范": ["公路桥涵施工技术规范", "混凝土结构工程施工规范"],
        "检测规范": ["公路桥梁技术状况评定标准", "桥梁检测规程"]
    },
    "施工工艺": {
        "施工方法": ["现浇施工", "预制安装", "顶推施工", "转体施工", "悬臂施工"],
        "质量控制": ["材料检验", "施工监控", "质量验收", "安全管理"]
    }
}

class BridgeEntityExtractor:
    def __init__(self):
        # Pre-compile regex for efficiency if using regex-based extraction
        # For now, simple string matching.
        self.ontology_terms: List[Tuple[str, str, str]] = [] # (term, category, sub_category)
        for category, sub_categories in BRIDGE_ENGINEERING_ONTOLOGY.items():
            for sub_category, terms in sub_categories.items():
                for term in terms:
                    self.ontology_terms.append((term, category, sub_category))
        # Sort by length descending to match longer terms first (e.g., "预应力混凝土" before "混凝土")
        self.ontology_terms.sort(key=lambda x: len(x[0]), reverse=True)

    def extract_professional_entities(self, text: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Extracts professional entities from text based on the BRIDGE_ENGINEERING_ONTOLOGY.
        Returns a dictionary where keys are main categories (e.g., "结构类型")
        and values are lists of found entity dictionaries, each containing:
        {'term': <matched_term>, 'sub_category': <sub_category_name>, 'category': <category_name>}
        """
        extracted_entities: Dict[str, List[Dict[str, str]]] = {
            category: [] for category in BRIDGE_ENGINEERING_ONTOLOGY.keys()
        }

        # To avoid duplicate matches of the exact same term at the exact same position
        # (though our current iteration doesn't store positions, this is good practice for future)
        # For now, we'll just add unique terms found.

        # More sophisticated matching would use NLP libraries for tokenization, lemmatization,
        # and potentially NER models trained on domain-specific data.
        # This is a basic keyword spotting approach.

        # Create a copy of the text to mark found entities and avoid re-matching substrings
        # This is a simple way to handle overlapping matches, e.g., "钢筋混凝土" vs "混凝土"
        # A better way would be non-overlapping matching or a more sophisticated NER tool.

        # For this version, let's find all occurrences.
        # If "预应力混凝土" is found, we still want to find "混凝土" if it appears alone elsewhere.

        found_terms_details = [] # Store (term, category, sub_category) to avoid duplicates in the final list for a type

        for term, category, sub_category in self.ontology_terms:
            # Use regex to find whole word matches, case-insensitive for flexibility
            # \b ensures that we match whole words, e.g. "钢" in "钢材" but not in "钢筋" if "钢" was a term
            try:
                # Iterate over all matches of the term in the text
                for match in re.finditer(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE):
                    # Storing the term itself, its sub_category, and main category
                    entity_detail = {
                        "term": match.group(0), # Use the matched term (to preserve case if using IGNORECASE)
                        "sub_category": sub_category,
                        "category": category,
                        # Could add 'start_char': match.start(), 'end_char': match.end() if needed
                    }
                    # Add to the main category list if not already effectively there
                    # (simple check to avoid exact duplicates if a term appears multiple times)
                    if entity_detail not in extracted_entities[category]:
                         extracted_entities[category].append(entity_detail)
            except re.error as e:
                print(f"Regex error for term '{term}': {e}")
                # Fallback to simple string search if regex fails for some term
                if term in text:
                    entity_detail = {
                        "term": term,
                        "sub_category": sub_category,
                        "category": category,
                    }
                    if entity_detail not in extracted_entities[category]:
                         extracted_entities[category].append(entity_detail)

        # Clean up empty categories
        return {k: v for k, v in extracted_entities.items() if v}

    def extract_relationships(self, text: str, entities: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
        """
        Extracts potential relationships between identified entities in the text.
        This is a placeholder for a more sophisticated relationship extraction mechanism.

        Args:
            text (str): The original text.
            entities (Dict[str, List[Dict[str, str]]]): Entities extracted by extract_professional_entities.
                                                        Each entity dict includes 'term', 'category', 'sub_category'.

        Returns:
            List[Dict[str, Any]]: A list of relationships, where each relationship could be
                                  {'subject': <entity_term1>, 'object': <entity_term2>, 'relation': <type_of_relation>,
                                   'subject_category': <cat1>, 'object_category': <cat2>, 'sentence': <context_sentence>}
        """
        # Placeholder implementation:
        # A very basic approach could be to look for co-occurrence of entities within the same sentence.
        # More advanced methods: dependency parsing, semantic role labeling, pattern matching, ML models.

        relationships = []

        # Flatten entities for easier iteration: list of (term, category, sub_category)
        all_extracted_terms = []
        for category_name, entity_list in entities.items():
            for entity_details in entity_list:
                all_extracted_terms.append({
                    "term": entity_details["term"],
                    "category": entity_details["category"],
                    "sub_category": entity_details["sub_category"]
                })

        if not all_extracted_terms or len(all_extracted_terms) < 2:
            return [] # Not enough entities to form relationships

        # Split text into sentences (simple split by period, question mark, exclamation mark)
        # A more robust sentence tokenizer should be used (e.g., from NLTK, spaCy)
        sentences = re.split(r'[.?!]', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        for sentence in sentences:
            sentence_entities = []
            for entity_info in all_extracted_terms:
                # Check if the entity term (as a whole word) is in the sentence
                if re.search(r'\b' + re.escape(entity_info["term"]) + r'\b', sentence, re.IGNORECASE):
                    sentence_entities.append(entity_info)

            if len(sentence_entities) >= 2:
                # If multiple entities are in the same sentence, assume some relationship.
                # This is a very naive assumption.
                # Create pairwise relationships for co-occurring entities in a sentence.
                for i in range(len(sentence_entities)):
                    for j in range(i + 1, len(sentence_entities)):
                        entity1 = sentence_entities[i]
                        entity2 = sentence_entities[j]

                        # Avoid relating an entity to itself if it appeared multiple times due to case variations
                        if entity1["term"].lower() == entity2["term"].lower() and entity1["category"] == entity2["category"]:
                            continue

                        # Define a generic relationship type, or try to infer based on categories
                        # For example, a "结构类型" might be "PART_OF" another "结构类型"
                        # Or a "材料类型" might be "USED_IN" a "结构类型"
                        # This requires more domain knowledge and rules.
                        relation_type = "RELATED_TO" # Generic relationship type

                        # Example rule: if a "材料类型" and "结构类型" co-occur, assume "USED_IN"
                        if (entity1["category"] == "材料类型" and entity2["category"] == "结构类型"):
                            relation_type = "USED_IN"
                            # Ensure direction: Material USED_IN Structure
                            relationships.append({
                                "subject": entity1["term"], "subject_details": entity1,
                                "object": entity2["term"], "object_details": entity2,
                                "relation": relation_type,
                                "context": sentence
                            })
                        elif (entity2["category"] == "材料类型" and entity1["category"] == "结构类型"):
                            relation_type = "USED_IN"
                            # Ensure direction: Material USED_IN Structure
                            relationships.append({
                                "subject": entity2["term"], "subject_details": entity2,
                                "object": entity1["term"], "object_details": entity1,
                                "relation": relation_type,
                                "context": sentence
                            })
                        # Example rule: if two "结构类型" co-occur, maybe "PART_OF" or "CONNECTED_TO"
                        elif (entity1["category"] == "结构类型" and entity2["category"] == "结构类型"):
                            relation_type = "STRUCTURALLY_RELATED_TO" # More generic for now
                            relationships.append({
                                "subject": entity1["term"], "subject_details": entity1,
                                "object": entity2["term"], "object_details": entity2,
                                "relation": relation_type,
                                "context": sentence
                            })
                        else: # Default generic relationship
                             relationships.append({
                                "subject": entity1["term"], "subject_details": entity1,
                                "object": entity2["term"], "object_details": entity2,
                                "relation": "CO_OCCURS_WITH", # A more descriptive generic relation
                                "context": sentence
                            })

        # Remove duplicate relationships (based on subject, object, relation type)
        unique_relationships = []
        seen_rels = set()
        for rel in relationships:
            # Create a unique key for the relationship, considering direction for some types
            # For CO_OCCURS_WITH, order doesn't matter as much. For others, it does.
            if rel["relation"] in ["CO_OCCURS_WITH", "STRUCTURALLY_RELATED_TO"]:
                rel_key_terms = tuple(sorted((rel["subject"].lower(), rel["object"].lower())))
                rel_key = (rel_key_terms[0], rel_key_terms[1], rel["relation"])
            else: # Order matters
                rel_key = (rel["subject"].lower(), rel["object"].lower(), rel["relation"])

            if rel_key not in seen_rels:
                unique_relationships.append(rel)
                seen_rels.add(rel_key)

        return unique_relationships


# Example Usage (can be removed or moved to a test file)
if __name__ == '__main__':
    extractor = BridgeEntityExtractor()
    sample_text_1 = "该项目的主要结构是预应力混凝土梁桥。施工中使用了高强混凝土和耐候钢。桥墩基础采用桩基。"
    sample_text_2 = "悬索桥的主缆连接到桥塔，桥面板由吊索支撑。设计规范遵循公路桥涵设计通用规范。"
    sample_text_3 = "桥梁检测规程要求对支座和伸缩缝进行定期检查。沥青路面需要维护。"

    print("--- Extracting entities from Sample Text 1 ---")
    entities1 = extractor.extract_professional_entities(sample_text_1)
    print(entities1)

    print("\n--- Extracting relationships from Sample Text 1 ---")
    relationships1 = extractor.extract_relationships(sample_text_1, entities1)
    print(relationships1)

    print("\n--- Extracting entities from Sample Text 2 ---")
    entities2 = extractor.extract_professional_entities(sample_text_2)
    print(entities2)

    print("\n--- Extracting relationships from Sample Text 2 ---")
    relationships2 = extractor.extract_relationships(sample_text_2, entities2)
    print(relationships2)

    print("\n--- Extracting entities from Sample Text 3 ---")
    entities3 = extractor.extract_professional_entities(sample_text_3)
    print(entities3)

    print("\n--- Extracting relationships from Sample Text 3 ---")
    relationships3 = extractor.extract_relationships(sample_text_3, entities3)
    print(relationships3)

    # Test with overlapping terms
    overlapping_text = "这是一个钢筋混凝土结构，使用了混凝土和钢筋。"
    print("\n--- Extracting entities from Overlapping Text ---")
    entities_overlap = extractor.extract_professional_entities(overlapping_text)
    # Expected: '混凝土' should be found, '钢筋' should be found.
    # '钢筋混凝土' is not in the ontology, so it won't be found as a single term.
    print(entities_overlap)
    # Check if both '钢筋' and '混凝土' are extracted under '材料类型'
    assert any(e['term'] == '混凝土' for e in entities_overlap.get('材料类型', []))
    assert any(e['term'] == '钢筋' for e in entities_overlap.get('材料类型', []))

    # Test with a term that is a substring of another
    substring_text = "预应力混凝土比普通混凝土强度高。"
    print("\n--- Extracting entities from Substring Text ---")
    entities_substring = extractor.extract_professional_entities(substring_text)
    print(entities_substring)
    # Expected: "预应力混凝土" and "普通混凝土" should be found.
    # Also, "混凝土" might be found separately if not handled by longest match first logic / non-overlapping.
    # My current implementation finds all occurrences, so "混凝土" would be found as part of the longer terms.
    # The sorting of ontology_terms by length helps prioritize longer matches if we were to consume text.
    # But re.finditer will find all non-overlapping instances of the *current* term.
    # This means "混凝土" will be found within "预应力混凝土" if "混凝土" is also a term.
    # Let's check the output.
    # The `ontology_terms` are sorted by length, but `re.finditer` for "混凝土" will still match inside "预应力混凝土".
    # The current output format: {'term': '预应力混凝土', ...}, {'term': '混凝土', ...}, {'term': '普通混凝土', ...}
    # This is acceptable as they are distinct terms from the ontology.

    found_terms_in_substring_test = [e['term'] for e in entities_substring.get('材料类型', [])]
    assert "预应力混凝土" in found_terms_in_substring_test
    assert "普通混凝土" in found_terms_in_substring_test
    assert "混凝土" in found_terms_in_substring_test # Because "混凝土" is itself an ontology term.

    print("\n--- Relationship extraction with overlapping terms in same sentence ---")
    # Example: "预应力混凝土梁使用了预应力混凝土和高强混凝土。"
    # Entities: "预应力混凝土梁" (if in ontology, currently not), "预应力混凝土", "高强混凝土"
    # Let's use actual ontology terms:
    text_rel_overlap = "悬索桥是一种梁桥，使用了钢材。" #梁桥, 悬索桥, 钢材
    entities_rel_overlap = extractor.extract_professional_entities(text_rel_overlap)
    print(entities_rel_overlap)
    relationships_rel_overlap = extractor.extract_relationships(text_rel_overlap, entities_rel_overlap)
    print(relationships_rel_overlap)
    # Expected: (悬索桥, RELATED_TO, 梁桥), (钢材, USED_IN, 悬索桥), (钢材, USED_IN, 梁桥)
    # The current relation extraction logic:
    # - STRUCTURALLY_RELATED_TO for two 结构类型
    # - USED_IN for 材料类型 and 结构类型
    # - CO_OCCURS_WITH for others.
    # So:
    # ('悬索桥', '梁桥', 'STRUCTURALLY_RELATED_TO')
    # ('钢材', '悬索桥', 'USED_IN')
    # ('钢材', '梁桥', 'USED_IN')
    # Check this logic.

    # Example from problem description: "桥梁工程专业实体识别升级"
    # "悬索桥", "斜拉桥", "梁桥", "拱桥", "刚构桥", "桁架桥", "组合桥"
    # "主梁", "横梁", "桥面板", "栏杆", "伸缩缝"
    # "桥墩", "桥台", "基础", "承台", "桩基"
    # "支座", "防撞护栏", "排水系统", "照明系统"
    # "钢材", "混凝土", "预应力钢绞线", "钢筋", "沥青"
    # ... etc.

    # A text like: "这座悬索桥的主梁采用了特殊钢材。"
    # Entities: 悬索桥 (结构类型/桥梁类型), 主梁 (结构类型/上部结构), 钢材 (材料类型/主要材料)
    # Relationships:
    #   主梁 PART_OF 悬索桥 (heuristic: 上部结构 is part of 桥梁类型)
    #   钢材 USED_IN 主梁 (heuristic: 材料类型 used in 结构类型)
    #   钢材 USED_IN 悬索桥 (heuristic: 材料类型 used in 结构类型)
    # My current extract_relationships is simpler:
    #   (主梁, 悬索桥, STRUCTURALLY_RELATED_TO)
    #   (钢材, 主梁, USED_IN)
    #   (钢材, 悬索桥, USED_IN)
    # This seems like a reasonable first step.

    print("BridgeEntityExtractor basic implementation complete.")
