from typing import Dict, List

class ConstructionWorkflowEngine:
    def __init__(self):
        self.workflow_templates = {} # Stores predefined workflow templates
        self.process_library = {}    # Stores library of individual processes/activities
        # Example: Load from a database or configuration files in a real app
        self._load_example_templates_and_library()

    def _load_example_templates_and_library(self):
        # Placeholder for loading some example data
        self.process_library = {
            "P001": {"id": "P001", "name": "基坑开挖", "duration_days": 5, "resources": ["excavator", "crew_A"], "category": "基础施工"},
            "P002": {"id": "P002", "name": "钻孔灌注桩", "duration_days": 15, "resources": ["drilling_rig", "crew_B"], "category": "基础施工", "depends_on": ["P001"]},
            "P003": {"id": "P003", "name": "承台施工", "duration_days": 10, "resources": ["concrete_mixer", "crew_A"], "category": "基础施工", "depends_on": ["P002"]},
            "P004": {"id": "P004", "name": "墩柱施工", "duration_days": 20, "resources": ["crane", "formwork_team"], "category": "下部结构", "depends_on": ["P003"]},
            "P005": {"id": "P005", "name": "现浇梁预制", "duration_days": 30, "resources": ["casting_yard_team"], "category": "上部结构"}, # Independent start possible
            "P006": {"id": "P006", "name": "现浇梁安装", "duration_days": 10, "resources": ["heavy_crane", "erection_team"], "category": "上部结构", "depends_on": ["P004", "P005"]},
        }
        self.workflow_templates = {
            "small_concrete_bridge_cast_in_situ": {
                "name": "小型混凝土现浇桥梁标准流程",
                "project_type_keywords": ["小型桥梁", "混凝土", "现浇"],
                "method_keywords": ["现浇"],
                "process_ids": ["P001", "P002", "P003", "P004", "P005", "P006"], # Ordered sequence for simplicity here
                "critical_processes_default": ["P002", "P004", "P006"] # Example critical items
            }
        }

    def define_construction_workflow(self, project_type: str, construction_method: str) -> Dict:
        """
        定义施工工艺流程.
        根据项目类型和施工方法从模板库选择或生成一个工作流.
        Placeholder: Simple keyword matching against templates.
        """
        # Normalize inputs for matching
        pt_lower = project_type.lower()
        cm_lower = construction_method.lower()

        for template_id, template_data in self.workflow_templates.items():
            pt_match = any(kw.lower() in pt_lower for kw in template_data.get("project_type_keywords", []))
            cm_match = any(kw.lower() in cm_lower for kw in template_data.get("method_keywords", []))

            if pt_match and cm_match:
                # Found a template, now construct the workflow details from process_library
                workflow_activities = []
                for process_id in template_data.get("process_ids", []):
                    if process_id in self.process_library:
                        workflow_activities.append(self.process_library[process_id].copy()) # Use a copy

                return {
                    "workflow_id": template_id,
                    "name": template_data.get("name"),
                    "project_type": project_type,
                    "construction_method": construction_method,
                    "activities": workflow_activities, # These are ordered as per template for now
                    "source": "template_based"
                }

        return {
            "workflow_id": "custom_workflow_placeholder",
            "name": f"自定义流程: {project_type} - {construction_method}",
            "project_type": project_type,
            "construction_method": construction_method,
            "activities": [], # In a real system, this might trigger a more complex generation
            "source": "generated_placeholder",
            "message": "No exact template match. Returning a placeholder. Further logic needed for custom generation."
        }

    def sequence_construction_activities(self, activities: List[Dict]) -> List[Dict]:
        """
        排序施工活动.
        基于逻辑关系 (e.g., 'depends_on') 和约束条件排序.
        Placeholder: Uses topological sort if 'depends_on' is present. Assumes activities have 'id'.
        """
        if not activities:
            return []

        # Build adjacency list and in-degree count for topological sort
        adj = {act['id']: [] for act in activities}
        in_degree = {act['id']: 0 for act in activities}

        activity_map = {act['id']: act for act in activities}

        for act in activities:
            dependencies = act.get('depends_on', [])
            if isinstance(dependencies, str): # If depends_on is a single string ID
                dependencies = [dependencies]

            for dep_id in dependencies:
                if dep_id in adj and act['id'] in activity_map: # Ensure dependency exists
                    adj[dep_id].append(act['id'])
                    in_degree[act['id']] += 1

        # Queue for nodes with in-degree 0
        queue = [act_id for act_id, degree in in_degree.items() if degree == 0]
        sorted_activities_ids = []

        while queue:
            u_id = queue.pop(0)
            sorted_activities_ids.append(u_id)

            for v_id in adj.get(u_id, []):
                in_degree[v_id] -= 1
                if in_degree[v_id] == 0:
                    queue.append(v_id)

        if len(sorted_activities_ids) == len(activities):
            # Return activities in the sorted order
            return [activity_map[act_id] for act_id in sorted_activities_ids]
        else:
            # Cycle detected or missing dependencies, return original with an error/warning
            # For simplicity, returning original. A robust system would flag the cycle.
            # You could add a status field to the activities or the return dict.
            # This also doesn't handle activities not part of the main dependency graph well.
            # For now, just return based on sorted IDs found, others appended if any left.
            sorted_list = [activity_map[act_id] for act_id in sorted_activities_ids]
            remaining_acts = [act for act in activities if act['id'] not in sorted_activities_ids]
            return sorted_list + remaining_acts # Potentially problematic if cycle exists

    def identify_critical_processes(self, workflow: Dict) -> List[Dict]:
        """
        识别关键工序.
        基于质量、安全、进度影响识别关键控制点.
        Placeholder: Uses default from template if available, or simple heuristics (e.g., longest duration).
        """
        critical_processes = []
        activities = workflow.get("activities", [])
        if not activities:
            return []

        # Attempt to use default critical processes from the template source
        workflow_id = workflow.get("workflow_id")
        if workflow_id and workflow_id in self.workflow_templates:
            default_critical_ids = self.workflow_templates[workflow_id].get("critical_processes_default", [])
            for act in activities:
                if act.get("id") in default_critical_ids:
                    cp = act.copy()
                    cp["criticality_reason"] = "Marked as critical by default in template."
                    critical_processes.append(cp)
            if critical_processes: # If found via template default
                return critical_processes

        # Fallback heuristic: e.g., processes with longest duration or most dependencies
        # This is a very simplified Critical Path Method (CPM) stand-in.
        # A full CPM would calculate Early Start, Early Finish, Late Start, Late Finish, Slack.

        # Simple heuristic: top 2 longest duration activities if no template default
        if not critical_processes and activities:
            sorted_by_duration = sorted(activities, key=lambda x: x.get("duration_days", 0), reverse=True)
            for i, act in enumerate(sorted_by_duration):
                if i < 2: # Mark top 2 as critical for this placeholder
                    cp = act.copy()
                    cp["criticality_reason"] = "Identified as critical by duration heuristic (placeholder)."
                    critical_processes.append(cp)
                else:
                    break

        return critical_processes

    def generate_process_templates(self, similar_projects_data: List[Dict]) -> Dict:
        """
        生成工艺模板.
        基于历史项目经验 (`similar_projects_data`) 生成标准化模板.
        Placeholder: Counts process occurrences and suggests a common sequence.
        `similar_projects_data` is a list of dicts, each representing a past project's workflow.
        Each project dict should have an "activities" list, with each activity having an "id" or "name".
        """
        if not similar_projects_data:
            return {"error": "No project data provided."}

        process_counts = {}
        process_sequences = [] # List of lists of process names/ids

        for project in similar_projects_data:
            activities = project.get("activities", [])
            current_sequence = []
            for act in activities:
                act_name = act.get("name", act.get("id")) # Prefer name, fallback to id
                if not act_name: continue

                process_counts[act_name] = process_counts.get(act_name, 0) + 1
                current_sequence.append(act_name)
            if current_sequence:
                process_sequences.append(current_sequence)

        if not process_counts:
            return {"info": "No common processes found or data insufficient."}

        # Determine common processes (e.g., those appearing in >50% of projects)
        most_common_processes = sorted(process_counts.items(), key=lambda x: x[1], reverse=True)

        # Placeholder for sequence generation:
        # A more advanced approach would use sequence alignment algorithms (e.g., from bioinformatics)
        # or frequent sequence mining.
        # For now, just list common processes.
        # A very naive "average" sequence could be the most frequent process first, etc.

        suggested_template = {
            "template_id": "generated_template_" + str(hash(str(similar_projects_data)))[:8],
            "name": "Generated Workflow Template (Placeholder)",
            "based_on_projects_count": len(similar_projects_data),
            "common_processes_by_frequency": most_common_processes,
            "suggested_sequence_note": "Sequence generation logic is a placeholder. Lists common processes.",
            "process_ids": [p[0] for p in most_common_processes if p[1] > len(similar_projects_data) * 0.5] # Example: must be in >50%
        }

        # Store it? For now, just return.
        # self.workflow_templates[suggested_template["template_id"]] = suggested_template
        return suggested_template

    def validate_workflow_feasibility(self, workflow: Dict, constraints: Dict) -> Dict:
        """
        验证工艺可行性.
        检查：资源可用性、技术可行性、时间合理性.
        `workflow` is a dict with "activities". `constraints` dict for resource limits, deadlines etc.
        Placeholder implementation.
        """
        activities = workflow.get("activities", [])
        if not activities:
            return {"is_feasible": True, "message": "No activities to validate."} # Or False if empty is not allowed

        results = {
            "is_feasible": True, # Assume true initially
            "resource_check": {"status": "OK", "details": []},
            "technical_check": {"status": "OK", "details": []}, # Needs domain knowledge
            "time_check": {"status": "OK", "details": []}
        }

        # 1. Resource Check (Simplified)
        # Assume constraints = {"available_resources": {"excavator": 1, "crew_A": 2, ...}, "max_duration_months": 6}
        # This needs a simulation or resource leveling algorithm for accuracy.
        # Simple check: do any activities require resources not in constraints?
        available_resources = constraints.get("available_resources", {})
        required_resources_overall = set()
        for act in activities:
            for res in act.get("resources", []):
                required_resources_overall.add(res)

        missing_resources = [res for res in required_resources_overall if res not in available_resources]
        if missing_resources:
            results["is_feasible"] = False
            results["resource_check"]["status"] = "Failed"
            results["resource_check"]["details"].append(f"Missing resource definitions in constraints: {missing_resources}")

        # This doesn't check for overallocation over time, just definition.

        # 2. Technical Check (Very Abstract Placeholder)
        # This would involve domain-specific rules, e.g., "Process X cannot be done in winter"
        # or "Technology Y requires soil_type Z".
        # For now, just a pass.
        if workflow.get("construction_method") == "UnsupportedMethodExample":
             results["is_feasible"] = False
             results["technical_check"]["status"] = "Failed"
             results["technical_check"]["details"].append("Construction method 'UnsupportedMethodExample' is technically not feasible for this placeholder.")

        # 3. Time Check (Simplified)
        # Calculate total duration based on a simple sequence (if not properly sequenced with dependencies)
        # Or, if sequenced, the duration of the longest path (critical path).
        total_duration_days = 0
        # If activities are already sequenced (e.g., by `sequence_construction_activities`)
        # and have 'depends_on', a proper CPM would be needed.
        # For a simple sum (assuming sequential or an estimate):
        for act in activities:
            total_duration_days += act.get("duration_days", 0)

        # This is a naive sum, not a CPM. If using CPM, use the project completion time.
        # For this placeholder, let's assume `total_duration_days` is a rough estimate.

        max_duration_days_constraint = constraints.get("max_duration_months", 0) * 30 # Approximate
        if max_duration_days_constraint > 0 and total_duration_days > max_duration_days_constraint:
            results["is_feasible"] = False
            results["time_check"]["status"] = "Failed"
            results["time_check"]["details"].append(f"Estimated duration {total_duration_days} days exceeds constraint of {max_duration_days_constraint} days.")

        if results["is_feasible"]:
            results["message"] = "Workflow appears feasible based on placeholder checks."
        else:
            results["message"] = "Workflow has potential feasibility issues."

        return results
