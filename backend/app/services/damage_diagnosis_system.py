from typing import Dict, List

class DamageDiagnosisSystem:
    def __init__(self):
        self.damage_knowledge_base: Dict[str, Dict] = {} # Example: {"裂缝": {"causes": [], "symptoms": []}}
        self.diagnosis_rules: Dict[str, callable] = {} # Example: {"rule_name": lambda data: True}
        # Pre-populate with some basic knowledge or rules if necessary
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        # This is a placeholder for loading or defining the knowledge base and rules
        # In a real system, this might load from a file, database, or be more complex.
        self.damage_knowledge_base = {
            "裂缝": {
                "common_causes": ["荷载过大", "温度变化", "材料收缩"],
                "typical_symptoms": ["可见裂纹", "结构变形"],
                "severity_levels": {"轻微": "宽度 < 0.2mm", "中等": "0.2mm <= 宽度 < 1mm", "严重": "宽度 >= 1mm"}
            },
            "锈蚀": {
                "common_causes": ["水分侵入", "氯离子腐蚀", "保护层失效"],
                "typical_symptoms": ["表面红褐色锈迹", "体积膨胀", "钢筋截面减小"],
                "severity_levels": {"轻微": "表面浮锈", "中等": "片状锈蚀", "严重": "锈坑，截面损失"}
            }
            # Add more damage types and their characteristics
        }
        # Define some simple rules
        self.diagnosis_rules["裂缝宽度规则"] = self._rule_crack_width_severity
        self.diagnosis_rules["锈蚀外观规则"] = self._rule_corrosion_appearance_severity

    def _rule_crack_width_severity(self, inspection_data: Dict) -> str:
        width = inspection_data.get("crack_width_mm")
        if width is None:
            return "未知"
        if width < 0.2:
            return "轻微"
        elif width < 1:
            return "中等"
        else:
            return "严重"

    def _rule_corrosion_appearance_severity(self, inspection_data: Dict) -> str:
        appearance = inspection_data.get("corrosion_appearance")
        if appearance == "表面浮锈":
            return "轻微"
        elif appearance == "片状锈蚀":
            return "中等"
        elif appearance == "锈坑":
            return "严重"
        return "未知"

    def identify_damage_type(self, inspection_data: Dict) -> List[Dict]:
        # 识别损伤类型
        # 基于检测数据和专家知识进行损伤识别
        # Placeholder: simple keyword matching or rule application
        identified_damages = []
        description = inspection_data.get("description", "").lower()

        if "裂缝" in description or "crack" in description:
            damage_info = {"type": "裂缝", "source_data": inspection_data}
            if "混凝土" in description:
                damage_info["material"] = "混凝土"
            identified_damages.append(damage_info)

        if "锈蚀" in description or "corrosion" in description or "rust" in description:
            damage_info = {"type": "锈蚀", "source_data": inspection_data}
            if "钢筋" in description or "steel" in description:
                damage_info["material"] = "钢结构"
            identified_damages.append(damage_info)

        # If no specific types identified, return a generic message or an empty list
        if not identified_damages:
            return [{"type": "未知损伤", "details": "未能根据提供的数据识别特定损伤类型"}]

        return identified_damages

    def assess_damage_severity(self, damage_info: Dict) -> Dict:
        # 评估损伤严重程度
        # 输出：轻微、中等、严重、危险等级
        # Placeholder: uses predefined rules or knowledge base
        damage_type = damage_info.get("type")
        inspection_data = damage_info.get("source_data", {})
        severity = "未知"

        if damage_type == "裂缝":
            severity = self._rule_crack_width_severity(inspection_data)
        elif damage_type == "锈蚀":
            severity = self._rule_corrosion_appearance_severity(inspection_data)

        return {
            "damage_type": damage_type,
            "assessed_severity": severity,
            "criteria_used": f"Rule based on {damage_type} characteristics" if severity != "未知" else "No specific rule applied"
        }

    def analyze_damage_causes(self, damage_pattern: Dict, environmental_factors: Dict) -> List[Dict]:
        # 分析损伤成因
        # 考虑：设计因素、施工因素、材料因素、环境因素、使用因素
        # Placeholder: uses knowledge base
        damage_type = damage_pattern.get("type")
        possible_causes = []

        if damage_type in self.damage_knowledge_base:
            causes_from_kb = self.damage_knowledge_base[damage_type].get("common_causes", [])
            for cause in causes_from_kb:
                possible_causes.append({"cause": cause, "source": "Knowledge Base"})

        if environmental_factors:
            for factor, value in environmental_factors.items():
                possible_causes.append({"cause": f"环境因素: {factor} - {value}", "source": "Environmental Data"})

        if not possible_causes:
            return [{"cause": "未知成因", "details": "未能确定具体成因"}]

        return possible_causes

    def predict_damage_development(self, current_state: Dict, conditions: Dict) -> Dict:
        # 预测损伤发展趋势
        # 基于劣化模型和环境条件预测损伤发展
        # Placeholder: simple logic
        damage_type = current_state.get("type")
        current_severity = current_state.get("assessed_severity")
        prediction = "发展趋势未知"

        if current_severity == "严重" or current_severity == "危险":
            prediction = "预计将快速恶化，建议立即处理"
        elif current_severity == "中等":
            if conditions.get("high_humidity", False) or conditions.get("heavy_traffic", False):
                prediction = "预计将持续发展，建议密切监测并计划修复"
            else:
                prediction = "预计将缓慢发展，建议定期监测"
        elif current_severity == "轻微":
            prediction = "预计发展缓慢，建议常规监测"

        return {
            "damage_type": damage_type,
            "current_severity": current_severity,
            "predicted_trend": prediction,
            "factors_considered": list(conditions.keys())
        }

    def recommend_inspection_strategy(self, bridge_info: Dict, damage_history: List[Dict]) -> Dict:
        # 推荐检测策略
        # 基于桥梁特点和损伤历史制定检测计划
        # Placeholder: basic recommendations
        recommendations = ["进行常规目视检测"]
        has_severe_damage_history = any(d.get("severity") in ["严重", "危险"] for d in damage_history)

        if bridge_info.get("age_years", 0) > 30 or has_severe_damage_history:
            recommendations.append("建议进行结构详细检测")

        if any("裂缝" in d.get("type", "") for d in damage_history):
            recommendations.append("重点关注裂缝发展情况，使用裂缝宽度尺测量")

        if any("锈蚀" in d.get("type", "") for d in damage_history):
            recommendations.append("检查钢结构防腐涂层，评估锈蚀程度")

        return {
            "bridge_id": bridge_info.get("id", "N/A"),
            "recommended_actions": recommendations,
            "basis": "Based on bridge age and damage history."
        }

# Example usage (optional, for testing or demonstration)
if __name__ == '__main__':
    diagnosis_system = DamageDiagnosisSystem()

    print("\n--- Identifying Damage Type ---")
    sample_inspection_data_crack = {"description": "主梁下缘发现混凝土裂缝，宽度约0.5mm", "crack_width_mm": 0.5}
    identified = diagnosis_system.identify_damage_type(sample_inspection_data_crack)
    print(identified)

    sample_inspection_data_rust = {"description": "钢桁架节点表面有片状锈蚀", "corrosion_appearance": "片状锈蚀"}
    identified_rust = diagnosis_system.identify_damage_type(sample_inspection_data_rust)
    print(identified_rust)

    print("\n--- Assessing Damage Severity ---")
    if identified and identified[0].get("type") != "未知损伤":
        # Pass the original inspection data along with the identified type for context
        damage_to_assess = {"type": identified[0]["type"], "source_data": sample_inspection_data_crack}
        severity = diagnosis_system.assess_damage_severity(damage_to_assess)
        print(severity)

    if identified_rust and identified_rust[0].get("type") != "未知损伤":
        damage_to_assess_rust = {"type": identified_rust[0]["type"], "source_data": sample_inspection_data_rust}
        severity_rust = diagnosis_system.assess_damage_severity(damage_to_assess_rust)
        print(severity_rust)


    print("\n--- Analyzing Damage Causes ---")
    if identified and identified[0].get("type") != "未知损伤":
        causes = diagnosis_system.analyze_damage_causes(
            identified[0],
            {"humidity": "high", "temperature_variation": "large"}
        )
        print(causes)

    print("\n--- Predicting Damage Development ---")
    # severity_result would come from a previous call to assess_damage_severity
    # For this example, we'll use the 'severity' dict obtained above if it exists
    if 'severity' in locals() and severity.get("assessed_severity") != "未知":
        prediction = diagnosis_system.predict_damage_development(
            {"type": severity["damage_type"], "assessed_severity": severity["assessed_severity"]},
            {"high_humidity": True, "heavy_traffic": True}
        )
        print(prediction)
    else:
        # Fallback if severity assessment was not conclusive for the first example
        prediction_fallback = diagnosis_system.predict_damage_development(
            {"type": "裂缝", "assessed_severity": "中等"},
            {"high_humidity": True, "heavy_traffic": True}
        )
        print(f"Fallback prediction: {prediction_fallback}")


    print("\n--- Recommending Inspection Strategy ---")
    strategy = diagnosis_system.recommend_inspection_strategy(
        {"id": "Bridge001", "age_years": 25, "type": "混凝土梁桥"},
        [{"type": "裂缝", "severity": "轻微", "date": "2022-01-01"}, {"type": "支座老化", "severity": "中等", "date":"2023-01-01"}]
    )
    print(strategy)

    strategy_old_bridge = diagnosis_system.recommend_inspection_strategy(
        {"id": "Bridge002", "age_years": 50},
        [{"type": "锈蚀", "severity": "严重", "date": "2023-06-01"}]
    )
    print(strategy_old_bridge)
