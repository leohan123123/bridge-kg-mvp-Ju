BRIDGE_ENTITIES = {
    "桥梁类型": ["悬索桥", "斜拉桥", "梁桥", "拱桥", "刚构桥", "桁架桥"],
    "材料": ["钢材", "混凝土", "预应力", "钢筋", "水泥", "沥青"],
    "结构": ["主梁", "桥墩", "基础", "桥台", "伸缩缝", "支座"],
    "规范": ["公路桥涵", "铁路桥梁", "设计规范", "施工规范", "验收规范"]
}

def extract_entities(text: str) -> dict:
    """
    Extracts bridge engineering entities from text using simple keyword matching.

    Args:
        text: The input text to analyze.

    Returns:
        A dictionary where keys are entity types and values are lists of found entities.
    """
    if not text:
        return {entity_type: [] for entity_type in BRIDGE_ENTITIES}

    found_entities = {entity_type: [] for entity_type in BRIDGE_ENTITIES}

    for entity_type, keywords in BRIDGE_ENTITIES.items():
        for keyword in keywords:
            if keyword in text:
                if keyword not in found_entities[entity_type]: # Avoid duplicate entries
                    found_entities[entity_type].append(keyword)

    return found_entities
