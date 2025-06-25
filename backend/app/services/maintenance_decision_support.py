from typing import Dict, List, Any

class MaintenanceDecisionSupport:
    def __init__(self):
        # Initialize with predefined maintenance strategies and cost models
        # These would typically be loaded from a configuration file or database
        self.maintenance_strategies: Dict[str, Dict[str, Any]] = {
            "preventive": {"cost_factor": 1, "priority_bonus": 0, "description": "Preventive Maintenance"},
            "corrective_minor": {"cost_factor": 2, "priority_bonus": 2, "description": "Corrective Maintenance (Minor)"},
            "corrective_major": {"cost_factor": 5, "priority_bonus": 5, "description": "Corrective Maintenance (Major)"},
            "replacement": {"cost_factor": 10, "priority_bonus": 3, "description": "Component Replacement"}
        }
        self.cost_models: Dict[str, float] = {
            "base_inspection_cost": 1000.0,
            "base_repair_unit_cost": 500.0,
            # More detailed cost models can be added here
        }

    def generate_maintenance_plan(self, bridge_condition: Dict, budget_constraints: Dict) -> Dict:
        # 生成维护计划
        # 基于桥梁状况和预算约束制定维护方案
        # Placeholder: Simple logic based on overall condition and budget
        plan = {"actions": [], "estimated_cost": 0.0, "warnings": []}
        overall_condition = bridge_condition.get("overall_assessment", "good") # e.g., good, fair, poor
        available_budget = budget_constraints.get("max_budget", float('inf'))

        if overall_condition == "poor":
            plan["actions"].append({"action_type": "corrective_major", "description": "Address critical structural issues"})
            plan["estimated_cost"] += self.cost_models.get("base_repair_unit_cost", 500) * self.maintenance_strategies["corrective_major"]["cost_factor"]
        elif overall_condition == "fair":
            plan["actions"].append({"action_type": "corrective_minor", "description": "Perform minor repairs and detailed inspection"})
            plan["estimated_cost"] += self.cost_models.get("base_repair_unit_cost", 500) * self.maintenance_strategies["corrective_minor"]["cost_factor"]
            plan["estimated_cost"] += self.cost_models.get("base_inspection_cost", 1000)
        else: # good condition
            plan["actions"].append({"action_type": "preventive", "description": "Routine preventive maintenance and inspection"})
            plan["estimated_cost"] += self.cost_models.get("base_inspection_cost", 1000) * self.maintenance_strategies["preventive"]["cost_factor"]

        if plan["estimated_cost"] > available_budget:
            plan["warnings"].append("Estimated cost exceeds available budget. Plan may need adjustment or phasing.")
            # Simple adjustment: defer some actions or choose cheaper alternatives (not implemented here)

        return plan

    def prioritize_maintenance_actions(self, maintenance_needs: List[Dict]) -> List[Dict]:
        # 维护行动优先级排序
        # 基于安全性、紧急性、经济性进行排序
        # Placeholder: Sort by a simple 'priority_score' (urgency + impact)

        def calculate_priority_score(need: Dict) -> float:
            urgency = need.get("urgency", 3)  # Scale 1-5 (5 is most urgent)
            safety_impact = need.get("safety_impact", 3) # Scale 1-5 (5 is highest impact)
            # economic_factor can be added if available, e.g., cost of inaction

            # Bonus from strategy type
            strategy_type = need.get("strategy_type", "preventive")
            priority_bonus = self.maintenance_strategies.get(strategy_type, {}).get("priority_bonus", 0)

            return (urgency * 0.5 + safety_impact * 0.5) + priority_bonus

        # Add a score to each need for sorting
        for need in maintenance_needs:
            need["priority_score"] = calculate_priority_score(need)

        # Sort by priority_score in descending order (higher score = higher priority)
        prioritized_list = sorted(maintenance_needs, key=lambda x: x["priority_score"], reverse=True)
        return prioritized_list

    def optimize_maintenance_timing(self, maintenance_activities: List[Dict]) -> Dict:
        # 优化维护时机
        # 考虑交通影响、季节因素、资源可用性
        # Placeholder: Simple rules for timing
        optimized_schedule = {"activities": [], "notes": []}
        current_month = 5 # Assume May for example

        for activity in maintenance_activities:
            preferred_timing = "Anytime"
            activity_type = activity.get("type", "general_repair")

            if "external_painting" in activity_type or "concrete_curing" in activity_type:
                if 4 <= current_month <= 10: # April to October
                    preferred_timing = "Optimal season (Spring/Summer/Autumn)"
                else:
                    preferred_timing = "Suboptimal season (Winter), consider delay if possible"
                    optimized_schedule["notes"].append(f"Winter may affect {activity_type}.")

            if activity.get("minimize_traffic_disruption", False):
                preferred_timing += " - Schedule during off-peak hours or nighttime."

            activity["optimized_timing_recommendation"] = preferred_timing
            optimized_schedule["activities"].append(activity)

        if not maintenance_activities:
            optimized_schedule["notes"].append("No activities to schedule.")

        return optimized_schedule

    def evaluate_maintenance_effectiveness(self, maintenance_records: List[Dict]) -> Dict:
        # 评估维护效果
        # 分析维护后的性能改善和成本效益
        # Placeholder: Basic evaluation based on post-maintenance condition
        total_cost = sum(record.get("cost", 0) for record in maintenance_records)
        improvements = []
        issues_remaining = 0

        for record in maintenance_records:
            if record.get("post_condition_rating", 0) > record.get("pre_condition_rating", 0):
                improvements.append(f"Improved {record.get('item_maintained', 'N/A')} from {record.get('pre_condition_rating')} to {record.get('post_condition_rating')}")
            elif record.get("post_condition_rating", 0) < record.get("pre_condition_rating", 0):
                 issues_remaining +=1

        effectiveness_summary = "Partially Effective"
        if not issues_remaining and len(improvements) > 0:
            effectiveness_summary = "Effective"
        elif issues_remaining > len(improvements):
            effectiveness_summary = "Ineffective or new issues arose"

        return {
            "total_maintenance_cost": total_cost,
            "number_of_actions": len(maintenance_records),
            "improvements_achieved": improvements if improvements else ["No specific improvements logged."],
            "issues_remaining_or_new": issues_remaining,
            "overall_effectiveness_summary": effectiveness_summary
        }

    def predict_future_maintenance_needs(self, current_condition: Dict, usage_patterns: Dict) -> List[Dict]:
        # 预测未来维护需求
        # 基于当前状况和使用模式预测维护需求
        # Placeholder: Simple prediction based on age and traffic
        needs = []
        bridge_age = current_condition.get("age_years", 10)
        traffic_load = usage_patterns.get("daily_traffic_volume", "medium") # low, medium, high

        if bridge_age > 20:
            needs.append({"need": "Detailed structural inspection", "reason": "Age > 20 years", "priority": "High"})

        if traffic_load == "high":
            needs.append({"need": "Pavement condition check", "reason": "High traffic load", "priority": "Medium"})
            needs.append({"need": "Bearing and expansion joint inspection", "reason": "High traffic load", "priority": "Medium"})

        if not needs:
            needs.append({"need": "Routine inspection as per schedule", "reason": "Standard procedure", "priority": "Low"})

        return needs

# Example usage (optional, for testing or demonstration)
if __name__ == '__main__':
    mds = MaintenanceDecisionSupport()

    print("\n--- Generating Maintenance Plan ---")
    plan_fair = mds.generate_maintenance_plan(
        {"overall_assessment": "fair", "last_inspection_date": "2022-01-01"},
        {"max_budget": 5000}
    )
    print(f"Plan for 'fair' condition: {plan_fair}")

    plan_poor_low_budget = mds.generate_maintenance_plan(
        {"overall_assessment": "poor"},
        {"max_budget": 2000} # Lower than estimated cost for poor
    )
    print(f"Plan for 'poor' condition (low budget): {plan_poor_low_budget}")

    print("\n--- Prioritizing Maintenance Actions ---")
    needs_to_prioritize = [
        {"id": "action1", "description": "Repair critical crack", "urgency": 5, "safety_impact": 5, "strategy_type": "corrective_major"},
        {"id": "action2", "description": "Routine inspection", "urgency": 2, "safety_impact": 2, "strategy_type": "preventive"},
        {"id": "action3", "description": "Replace worn bearing", "urgency": 4, "safety_impact": 4, "strategy_type": "replacement"},
        {"id": "action4", "description": "Minor rust removal", "urgency": 3, "safety_impact": 2, "strategy_type": "corrective_minor"},
    ]
    prioritized_actions = mds.prioritize_maintenance_actions(needs_to_prioritize)
    print(f"Prioritized Actions: {[action['id'] for action in prioritized_actions]} with scores {[action.get('priority_score') for action in prioritized_actions]}")


    print("\n--- Optimizing Maintenance Timing ---")
    activities_to_schedule = [
        {"type": "external_painting", "duration_days": 5, "minimize_traffic_disruption": True},
        {"type": "deck_waterproofing", "duration_days": 3, "minimize_traffic_disruption": False},
        {"type": "general_repair", "duration_days": 2}
    ]
    optimized_timing = mds.optimize_maintenance_timing(activities_to_schedule)
    print(optimized_timing)

    print("\n--- Evaluating Maintenance Effectiveness ---")
    maintenance_history = [
        {"item_maintained": "Deck Joint A", "cost": 1200, "pre_condition_rating": 2, "post_condition_rating": 4, "date": "2023-01-15"},
        {"item_maintained": "Bearing B1", "cost": 3000, "pre_condition_rating": 1, "post_condition_rating": 5, "date": "2023-02-20"},
        {"item_maintained": "Surface Patch S3", "cost": 500, "pre_condition_rating": 3, "post_condition_rating": 3, "date": "2023-03-10"}, # No improvement
    ]
    effectiveness_eval = mds.evaluate_maintenance_effectiveness(maintenance_history)
    print(effectiveness_eval)

    print("\n--- Predicting Future Maintenance Needs ---")
    future_needs = mds.predict_future_maintenance_needs(
        {"age_years": 25, "material": "concrete"},
        {"daily_traffic_volume": "high", "climate": "temperate"}
    )
    print(future_needs)

    future_needs_new_bridge = mds.predict_future_maintenance_needs(
        {"age_years": 5, "material": "steel"},
        {"daily_traffic_volume": "low"}
    )
    print(future_needs_new_bridge)
