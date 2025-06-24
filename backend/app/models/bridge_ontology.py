BRIDGE_RAG_ONTOLOGY = {
    "entities": {
        "Bridge": {
            "properties": ["name", "type", "span_length", "location", "design_year", "description"],
            "index_fields": ["name", "type", "location"],  # RAG检索优化
            "embedding_fields": ["description"]  # 向量检索字段
        },
        "Material": {
            "properties": ["name", "type", "strength", "standard_code", "application"],
            "index_fields": ["name", "type", "standard_code"],
            "embedding_fields": ["application"]
        },
        "Component": {
            "properties": ["name", "function", "specifications", "design_principles"],
            "index_fields": ["name", "function"],
            "embedding_fields": ["design_principles"]
        },
        "Standard": {
            "properties": ["code", "title", "version", "scope", "requirements"],
            "index_fields": ["code", "title"],
            "embedding_fields": ["scope", "requirements"]
        },
        "Technique": {
            "properties": ["name", "method", "application_scenario", "advantages"],
            "index_fields": ["name", "method"],
            "embedding_fields": ["application_scenario", "advantages"]
        }
    },
    "relationships": {
        "USES_MATERIAL": {"properties": ["usage_purpose", "quantity"]},
        "CONTAINS_COMPONENT": {"properties": ["location", "function"]},
        "FOLLOWS_STANDARD": {"properties": ["compliance_level", "version"]},
        "APPLIES_TECHNIQUE": {"properties": ["stage", "purpose"]},
        "RELATED_TO": {"properties": ["relationship_type", "strength"]}
    }
}
