from typing import Dict, List, Any, Callable
import re

# Define a type for a calculation function
# It takes a dictionary of parameters and returns a dictionary of results
CalculationFunction = Callable[[Dict[str, float]], Dict[str, float]]

class DesignCalculationEngine:
    def __init__(self):
        self.calculation_methods: Dict[str, Dict[str, Any]] = {}
        # Example calculation_methods entry:
        # "beam_bending_moment": {
        #     "description": "Calculates maximum bending moment for a simply supported beam with point load.",
        #     "parameters": ["point_load_P (kN)", "span_L (m)"],
        #     "outputs": ["max_moment_M (kNm)"],
        #     "formula_str": "M = P * L / 4",
        #     "calculation_function": self._calculate_beam_bending_moment # Reference to actual function
        # }
        self.formula_database: Dict[str, Dict[str, Any]] = {} # Stores formula metadata
        # Example formula_database entry:
        # "BM_SIMPLE_BEAM_POINT_LOAD": {
        #     "expression": "M = P * L / 4",
        #     "variables": ["P", "L", "M"],
        #     "description": "Max bending moment, simply supported beam, central point load",
        #     "related_methods": ["beam_bending_moment"]
        # }

    def register_calculation_method(self, method_name: str, method_info: Dict[str, Any],
                                    calc_function: CalculationFunction = None) -> bool:
        """
        Registers a calculation method.
        method_info should include: description, parameters (list of names/units), outputs (list of names/units).
        calc_function is the actual Python function to perform the calculation.
        """
        if method_name in self.calculation_methods:
            print(f"Warning: Calculation method '{method_name}' already exists. Overwriting.")

        required_keys = ["description", "parameters", "outputs"]
        if not all(key in method_info for key in required_keys):
            print(f"Error: Method info for '{method_name}' is incomplete. Missing one of {required_keys}.")
            return False

        self.calculation_methods[method_name] = {
            "description": method_info["description"],
            "parameters": method_info["parameters"], # e.g., ["load (kN)", "span (m)"]
            "outputs": method_info["outputs"],       # e.g., ["moment (kNm)"]
            "formula_str": method_info.get("formula_str", "N/A"), # Optional: string representation of formula
            "calculation_function": calc_function # The actual function
        }

        # Optionally, also add to formula_database if formula_str is provided
        if "formula_str" in method_info and method_info["formula_str"] != "N/A":
            formula_id = method_info.get("formula_id", method_name.upper() + "_FORMULA")
            self.formula_database[formula_id] = {
                "expression": method_info["formula_str"],
                "variables": self._extract_variables_from_formula_str(method_info["formula_str"]),
                "description": method_info.get("description", ""),
                "related_methods": [method_name]
            }
        return True

    def _extract_variables_from_formula_str(self, formula_str: str) -> List[str]:
        # Simple extraction of uppercase words or single letters as variables
        # This is a basic placeholder. A more robust parser would be needed for complex formulas.
        return list(set(re.findall(r'\b([A-Z][a-zA-Z0-9_]*|[A-Za-z])\b', formula_str)))


    def execute_calculation(self, method_name: str, params: Dict[str, float]) -> Dict[str, Any]:
        """
        Executes a registered calculation method.
        params: A dictionary of parameter names and their values, e.g., {"point_load_P": 100, "span_L": 5}
        """
        if method_name not in self.calculation_methods:
            return {"error": f"Calculation method '{method_name}' not found."}

        method_data = self.calculation_methods[method_name]
        calc_func = method_data.get("calculation_function")

        if not calc_func:
            return {"error": f"No calculation function implemented for method '{method_name}'."}

        # Basic parameter validation (check if all required parameters are provided)
        # Assumes parameters in method_data["parameters"] are like "name (unit)" or just "name"
        required_param_names = [p.split(' ')[0] for p in method_data["parameters"]]

        missing_params = [p_name for p_name in required_param_names if p_name not in params]
        if missing_params:
            return {"error": f"Missing parameters for '{method_name}': {', '.join(missing_params)}"}

        try:
            # Filter params to only those required by the function if needed, or pass all
            # For now, pass all provided params. The function should pick what it needs.
            results = calc_func(params)
            return {"success": True, "method": method_name, "inputs": params, "results": results}
        except Exception as e:
            return {"error": f"Error during calculation for '{method_name}': {str(e)}"}


    def extract_calculation_workflows(self, design_documents: List[str]) -> List[Dict[str, Any]]:
        """
        Placeholder: Extracts calculation workflows from design documents.
        This would involve NLP to identify sequences of calculations, data dependencies, and decision points.
        """
        workflows = []
        # Example workflow structure:
        # {
        #   "name": "BeamCapacityCheckWorkflow",
        #   "steps": [
        #     {"sequence": 1, "method": "calculate_bending_moment", "inputs_from": "initial_params"},
        #     {"sequence": 2, "method": "calculate_shear_force", "inputs_from": "initial_params"},
        #     {"sequence": 3, "method": "check_moment_capacity", "inputs_from": ["step1_results", "material_props"]},
        #     {"sequence": 4, "decision": "if_moment_ok", "true_next": 5, "false_next": "report_failure"}
        #   ],
        #   "data_flow": {...}
        # }
        for doc_index, doc_content in enumerate(design_documents):
            if "workflow for beam design" in doc_content.lower(): # Very naive trigger
                workflows.append({
                    "name": f"SampleBeamWorkflow_Doc{doc_index+1}",
                    "description": "A conceptual workflow for beam design.",
                    "steps": [
                        {"step": 1, "action": "Define beam geometry and loads", "details": "L, w, P"},
                        {"step": 2, "action": "Calculate max bending moment (M_max)", "method_hint": "beam_bending_moment"},
                        {"step": 3, "action": "Calculate max shear force (V_max)", "method_hint": "beam_shear_force"},
                        {"step": 4, "action": "Select material and section properties", "details": "fy, Zx"},
                        {"step": 5, "action": "Check bending capacity (M_u >= M_max)", "method_hint": "bending_capacity_check"},
                        {"step": 6, "action": "Check shear capacity (V_u >= V_max)", "method_hint": "shear_capacity_check"}
                    ],
                    "source_document_index": doc_index
                })
        return workflows

    def build_formula_relationships(self, formulas_input: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Builds relationships between formulas (e.g., basic -> derived).
        `formulas_input` is a list of formula dicts, e.g. from self.formula_database or external.
        This is a placeholder. Real implementation requires semantic understanding of formulas.
        """
        relationships: Dict[str, List[str]] = {"derived_from": [], "uses_concept_from": []}

        # Naive example: if one formula's variable is another formula's output (very simplified)
        formula_outputs: Dict[str, List[str]] = {} # formula_id -> list of output variables (e.g. 'M' from 'M = P*L/4')

        all_formulas = list(self.formula_database.values()) + formulas_input
        unique_formulas = {f["expression"]: f for f in all_formulas}.values() # Simple deduplication by expression

        for f_data in unique_formulas:
            expr = f_data.get("expression", "")
            f_id = f_data.get("id", expr) # Use expression as ID if no ID
            # Assume the variable on the left of '=' is the output
            match = re.match(r"\s*([A-Za-z][A-Za-z0-9_]*)\s*=", expr)
            if match:
                formula_outputs[f_id] = [match.group(1).strip()]
            else:
                formula_outputs[f_id] = []


        for f1_data in unique_formulas:
            f1_id = f1_data.get("id", f1_data.get("expression"))
            f1_vars = set(f1_data.get("variables", []))
            f1_outputs = set(formula_outputs.get(f1_id,[]))
            f1_inputs = f1_vars - f1_outputs # Variables not on the left side of '='

            for f2_data in unique_formulas:
                if f1_data.get("expression") == f2_data.get("expression"):
                    continue
                f2_id = f2_data.get("id", f2_data.get("expression"))
                f2_outputs = set(formula_outputs.get(f2_id,[]))

                # If an output of f2 is an input of f1, then f1 might be "derived from" or "uses" f2
                if f1_inputs.intersection(f2_outputs):
                    relationships["derived_from"].append({
                        "derived_formula_id": f1_id,
                        "base_formula_id": f2_id,
                        "shared_variable": list(f1_inputs.intersection(f2_outputs))[0]
                    })

        return relationships

    def validate_calculation_logic(self, calculation_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates a chain/sequence of calculations.
        `calculation_chain`: list of dicts, each representing a calculation step.
                           e.g., [{"method": "m1", "params": {...}}, {"method": "m2", "params_from_step1_output": "..."}]
        Checks for unit consistency (placeholder), numerical reasonability (placeholder), logical flow.
        """
        results = {"is_valid": True, "errors": [], "warnings": []}

        # Placeholder for unit consistency check (very complex in reality)
        # We'd need a unit library and knowledge of how units propagate through formulas.
        # For now, just a conceptual check.

        # Example: Check if outputs of one step are used as inputs in the next if specified.
        # This is a very basic data flow check.
        previous_step_outputs = {}
        for i, step in enumerate(calculation_chain):
            method_name = step.get("method")
            params = step.get("params", {})

            if not method_name or method_name not in self.calculation_methods:
                results["is_valid"] = False
                results["errors"].append(f"Step {i+1}: Method '{method_name}' not registered or not specified.")
                continue

            # Parameter source (e.g. from previous step) - simplified
            params_from_previous_key = step.get("params_from_previous_output_key") # e.g. "max_moment_M"
            if params_from_previous_key and previous_step_outputs:
                if params_from_previous_key in previous_step_outputs:
                    # Assume the value from previous output is directly used as one of the params.
                    # This is a simplification. Real mapping could be complex.
                    # Let's say the previous output is named 'X' and current step needs param 'A'.
                    # The chain spec would need to say "map X to A".
                    # For now, assume direct use if a key matches.
                    param_to_fill = step.get("param_to_fill_from_previous", params_from_previous_key) # e.g. "moment_input"
                    params[param_to_fill] = previous_step_outputs[params_from_previous_key]
                else:
                    results["is_valid"] = False
                    results["errors"].append(f"Step {i+1}: Expected output '{params_from_previous_key}' from previous step not found.")

            # Execute the calculation to get outputs for the next step (if any)
            # This is also for validation, not just execution.
            # We are not using the full `execute_calculation` here to avoid deep recursion or complex state.
            # This validation is more about the chain structure.
            method_spec = self.calculation_methods[method_name]
            required_param_names = [p.split(' ')[0] for p in method_spec["parameters"]]

            current_step_params_ok = True
            for p_name in required_param_names:
                if p_name not in params:
                    results["is_valid"] = False
                    results["errors"].append(f"Step {i+1} ('{method_name}'): Missing parameter '{p_name}'.")
                    current_step_params_ok = False

            if current_step_params_ok:
                # Mock execution for validation purposes
                # Assume all output variables are floats for now.
                # In reality, we'd call the function or have detailed metadata about output types.
                mock_outputs = {}
                for out_spec in method_spec["outputs"]: # e.g. "max_moment_M (kNm)"
                    out_name = out_spec.split(' ')[0]
                    mock_outputs[out_name] = 0.0 # Placeholder value
                previous_step_outputs = mock_outputs
            else:
                previous_step_outputs = {} # Cannot proceed with this path

        # Numerical reasonability (placeholder) - e.g., check if values are within expected ranges
        # This would require domain knowledge (e.g., steel yield strength typically 235-550 MPa)

        # Logical correctness (placeholder) - e.g., ensure prerequisite calculations are done.
        # (Partially covered by the data flow check above)

        return results

# Example Calculation Functions (to be registered)
def _calculate_beam_bending_moment_simple_point_load(params: Dict[str, float]) -> Dict[str, float]:
    P = params.get("point_load_P")
    L = params.get("span_L")
    if P is None or L is None:
        raise ValueError("Missing P or L for bending moment calculation.")
    M = P * L / 4.0
    return {"max_moment_M": M}

def _calculate_concrete_compressive_strength_design_value(params: Dict[str, float]) -> Dict[str, float]:
    f_ck = params.get("f_ck") # Characteristic compressive strength
    gamma_c = params.get("gamma_c", 1.5) # Partial safety factor for concrete
    if f_ck is None:
        raise ValueError("Missing f_ck for concrete strength calculation.")
    f_cd = f_ck / gamma_c
    return {"f_cd": f_cd}


# Example Usage
if __name__ == '__main__':
    engine = DesignCalculationEngine()

    # 1. Register calculation methods
    engine.register_calculation_method(
        "beam_bending_moment_SPL",
        {
            "description": "Max bending moment for simply supported beam, central point load.",
            "parameters": ["point_load_P (kN)", "span_L (m)"],
            "outputs": ["max_moment_M (kNm)"],
            "formula_str": "M = P * L / 4"
        },
        _calculate_beam_bending_moment_simple_point_load
    )
    engine.register_calculation_method(
        "concrete_strength_design",
        {
            "description": "Calculates design compressive strength of concrete.",
            "parameters": ["f_ck (MPa)", "gamma_c"], # gamma_c is unitless
            "outputs": ["f_cd (MPa)"],
            "formula_str": "f_cd = f_ck / gamma_c"
        },
        _calculate_concrete_compressive_strength_design_value
    )
    print("Registered methods:", list(engine.calculation_methods.keys()))
    print("Formula DB:", engine.formula_database)
    print("Variables for M=P*L/4:", engine._extract_variables_from_formula_str("M = P*L/4"))


    # 2. Execute a calculation
    moment_calc_result = engine.execute_calculation(
        "beam_bending_moment_SPL",
        {"point_load_P": 100.0, "span_L": 8.0}
    )
    print("\nMoment Calculation Result:", moment_calc_result)

    strength_calc_result = engine.execute_calculation(
        "concrete_strength_design",
        {"f_ck": 30.0} # gamma_c will use default if calc function handles it
    )
    print("Strength Calculation Result:", strength_calc_result)

    error_calc_result = engine.execute_calculation(
        "beam_bending_moment_SPL",
        {"point_load_P": 100.0} # Missing span_L
    )
    print("Error Calculation Result:", error_calc_result)


    # 3. Extract calculation workflows (mock)
    sample_doc = "This document outlines the workflow for beam design. First, calculate moments, then shear."
    workflows = engine.extract_calculation_workflows([sample_doc])
    print("\nExtracted Workflows:", workflows)

    # 4. Build formula relationships
    # Add another related formula for testing relationships
    engine.formula_database["SHEAR_SIMPLE_BEAM_POINT_LOAD"] = {
        "expression": "V = P / 2",
        "variables": ["V", "P"],
        "description": "Max shear force, simply supported beam, central point load"
    }
    # Assume M = P*L/4 uses P, and V = P/2 provides P (this is a contrived example for the logic)
    # Let's make it more direct: Formula A uses output of Formula B
    engine.formula_database["AREA_RECT"] = {"id": "AREA_RECT", "expression": "Area = Width * Height", "variables": ["Area", "Width", "Height"]}
    engine.formula_database["STRESS_AXIAL"] = {"id": "STRESS_AXIAL", "expression": "Stress = Force / Area", "variables": ["Stress", "Force", "Area"]}

    formula_relations = engine.build_formula_relationships([]) # Uses internal formula_database
    print("\nFormula Relationships:", formula_relations)


    # 5. Validate calculation logic (mock chain)
    valid_chain = [
        {"method": "beam_bending_moment_SPL", "params": {"point_load_P": 100.0, "span_L": 8.0}},
        # Assume next step uses output "max_moment_M" from previous.
        # For validation, we need a method that would take "max_moment_M" as input.
        # Let's define a dummy one for this test:
        {"method": "dummy_moment_consumer", "params_from_previous_output_key": "max_moment_M", "param_to_fill_from_previous": "moment_input"}
    ]
    # Register the dummy method for the chain validation to work
    def _dummy_consumer(params: Dict[str, float]) -> Dict[str, float]: return {"consumed": params.get("moment_input", 0)}
    engine.register_calculation_method("dummy_moment_consumer", {
        "description":"Consumes a moment value",
        "parameters":["moment_input (kNm)"],
        "outputs":["consumed_value (kNm)"]}, _dummy_consumer)

    chain_validation = engine.validate_calculation_logic(valid_chain)
    print("\nCalculation Chain Validation (Valid Chain):", chain_validation)

    invalid_chain = [
        {"method": "beam_bending_moment_SPL", "params": {"point_load_P": 100.0}}, # Missing span_L
        {"method": "concrete_strength_design", "params": {"f_ck": 30.0}}
    ]
    chain_validation_invalid = engine.validate_calculation_logic(invalid_chain)
    print("Calculation Chain Validation (Invalid Chain):", chain_validation_invalid)

    chain_with_bad_link = [
        {"method": "beam_bending_moment_SPL", "params": {"point_load_P": 100.0, "span_L": 8.0}},
        {"method": "dummy_moment_consumer", "params_from_previous_output_key": "non_existent_output", "param_to_fill_from_previous": "moment_input"}
    ]
    chain_validation_bad_link = engine.validate_calculation_logic(chain_with_bad_link)
    print("Calculation Chain Validation (Bad Link):", chain_validation_bad_link)
