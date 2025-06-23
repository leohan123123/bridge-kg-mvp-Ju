# backend/app/tests/services/test_data_preprocessor.py
import pytest
import copy # For deep copying mock data
from pathlib import Path

from ...services.data_preprocessor import DataPreprocessorService
# from backend.app.models.bridge_component import ComponentType # 如果需要比较枚举

# --- Mock Data Fixtures ---

@pytest.fixture
def mock_parsed_dxf_data_basic():
    """基本DXF解析数据，用于测试"""
    return {
        "metadata": {
            "dxf_version": "R2018",
            "filename": "test_bridge.dxf",
            "units": 4 # Millimeters
        },
        "layers": [{"name": "BEAMS", "color": 1}, {"name": "COLUMNS", "color": 2}],
        "bridge_components": [
            {
                "component_id": "BEAM_001",
                "component_type": "BEAM", # Corresponds to ComponentType.BEAM.value
                "name": "Beam B1",
                "layer": "BEAMS",
                "material": {"name": "混凝土", "grade": "C30"},
                "geometry_info": [{
                    "primitive_type": "LINE",
                    "coordinates": [[0.0,0.0,0.0], [10000.0,0.0,0.0]], # in mm
                    "length": 10000.0 # in mm
                }],
                "properties": {},
                "connections": []
            },
            {
                "component_id": "COLUMN_001",
                "component_type": "COLUMN",
                "name": "Column C1",
                "layer": "COLUMNS",
                "material": None, # 测试缺失材料处理
                "geometry_info": [{
                    "primitive_type": "LINE",
                    "coordinates": [[0.0,0.0,0.0], [0.0,0.0,3000.0]], # in mm
                    "length": 3000.0 # in mm
                }],
                "properties": {},
                "connections": []
            }
        ],
        "errors": []
    }

@pytest.fixture
def mock_parsed_dxf_data_with_duplicates_and_issues(mock_parsed_dxf_data_basic):
    """包含重复项、单位问题和几何问题的数据"""
    data = copy.deepcopy(mock_parsed_dxf_data_basic)
    # 添加重复构件
    duplicate_beam = copy.deepcopy(data["bridge_components"][0])
    duplicate_beam["component_id"] = "BEAM_001" # Same ID
    duplicate_beam["name"] = "Beam B1 Duplicate" # Different name to distinguish if needed
    data["bridge_components"].append(duplicate_beam)

    # 添加一个类型未知、无ID的构件
    data["bridge_components"].append({
        "component_id": None, # No ID
        "component_type": "UNKNOWN_FROM_TEST", # Test unknown type handling
        "name": "Unknown Component",
        "layer": "UnknownLayer",
        "material": {"name": "钢材", "grade": "Q235"},
        "geometry_info": [{
            "primitive_type": "CIRCLE", # mm
            "center": [500.0, 500.0, 0.0], "radius": 100.0, "area": 31415.926535 # mm^2
        }]
    })
    # 添加一个长度为零的线
    data["bridge_components"].append({
        "component_id": "ZERO_LEN_LINE_001",
        "component_type": "OTHER",
        "name": "Zero Length Line",
        "layer": "TEST_LINES",
        "material": {"name": "钢材", "grade": "Q235"},
        "geometry_info": [{
            "primitive_type": "LINE",
            "coordinates": [[1.0,1.0,1.0], [1.0,1.0,1.0]], # Zero length
            "length": 0.0
        }]
    })
    # 添加一个需要单位转换的 Polyline (mm)
    data["bridge_components"].append({
        "component_id": "POLY_001",
        "component_type": "SLAB",
        "name": "Poly Slab",
        "layer": "SLABS",
        "material": {"name": "混凝土", "grade": "C40"},
        "geometry_info": [{
            "primitive_type": "LWPOLYLINE",
            "coordinates": [[0,0,0], [2000,0,0], [2000,1000,0], [0,1000,0]], # in mm
            "length": None, # Test length calculation
            "is_closed": True
        }]
    })
    data["metadata"]["units"] = 4 # Millimeters
    return data

# --- Test Cases ---

def test_data_preprocessor_initialization(mock_parsed_dxf_data_basic):
    """测试服务初始化"""
    service = DataPreprocessorService(parsed_dxf_data=mock_parsed_dxf_data_basic)
    assert service.raw_data == mock_parsed_dxf_data_basic
    assert len(service.processed_data["bridge_components"]) == 2
    assert service.processed_data["metadata"]["filename"] == "test_bridge.dxf"

def test_initialization_with_missing_keys():
    """测试当输入数据缺少关键键时的初始化处理"""
    faulty_data = {"metadata": {"filename": "faulty.dxf"}} # Missing "bridge_components"
    service = DataPreprocessorService(parsed_dxf_data=faulty_data)
    assert any(err["type"] == "InitializationError" and "bridge_components" in err["message"] for err in service.processing_errors)
    assert "bridge_components" not in service.processed_data # or it's an empty list

def test_remove_duplicate_components(mock_parsed_dxf_data_with_duplicates_and_issues):
    """测试移除重复构件的逻辑"""
    service = DataPreprocessorService(parsed_dxf_data=mock_parsed_dxf_data_with_duplicates_and_issues)
    # 原始数据有5个构件 (2 original + 1 duplicate BEAM_001 + 1 UNKNOWN + 1 ZERO_LEN_LINE + 1 POLY) = 6
    # BEAM_001 (original), COLUMN_001, BEAM_001 (duplicate), UNKNOWN_COMP, ZERO_LEN_LINE_001, POLY_001
    assert len(service.raw_data["bridge_components"]) == 6

    service._remove_duplicate_components() # 直接调用内部方法进行测试

    # 应移除一个BEAM_001的副本，保留无ID的构件
    # Expected: BEAM_001, COLUMN_001, UNKNOWN_COMP, ZERO_LEN_LINE_001, POLY_001
    assert len(service.processed_data["bridge_components"]) == 5
    component_ids = [comp.get("component_id") for comp in service.processed_data["bridge_components"]]
    assert component_ids.count("BEAM_001") == 1
    assert any(err["type"] == "DataCleaning" and "BEAM_001" in err["message"] for err in service.processing_errors)
    # 检查无ID构件是否被保留并产生警告
    assert any(comp.get("name") == "Unknown Component" for comp in service.processed_data["bridge_components"])
    assert any(err["type"] == "DataWarning" and "没有component_id" in err["message"] for err in service.processing_errors)


def test_unit_conversion_mm_to_meters(mock_parsed_dxf_data_basic):
    """测试从毫米到米的单位转换"""
    data = copy.deepcopy(mock_parsed_dxf_data_basic)
    data["metadata"]["units"] = 4 # Millimeters

    service = DataPreprocessorService(parsed_dxf_data=data)
    service._convert_units(dxf_unit_code=4, target_unit_name="meters")

    beam_geom = service.processed_data["bridge_components"][0]["geometry_info"][0]
    column_geom = service.processed_data["bridge_components"][1]["geometry_info"][0]

    # 检查坐标转换
    assert beam_geom["coordinates"][1][0] == pytest.approx(10.0) # 10000mm -> 10m
    assert column_geom["coordinates"][1][2] == pytest.approx(3.0) # 3000mm -> 3m
    # 检查长度转换
    assert beam_geom["length"] == pytest.approx(10.0)
    assert column_geom["length"] == pytest.approx(3.0)

    assert service.processed_data["metadata"]["processed_units"] == "meters"
    assert service.processed_data["metadata"]["unit_conversion_factor_to_meters"] == 0.001

def test_unit_conversion_unitless(mock_parsed_dxf_data_basic):
    """测试Unitless单位的处理 (应发出警告，因子为1.0)"""
    data = copy.deepcopy(mock_parsed_dxf_data_basic)
    data["metadata"]["units"] = 0 # Unitless
    service = DataPreprocessorService(parsed_dxf_data=data)
    service._convert_units(dxf_unit_code=0, target_unit_name="meters")

    assert service.processed_data["metadata"]["unit_conversion_factor_to_meters"] == 1.0
    assert any(err["type"] == "UnitConversionWarning" and "Unitless" in err["message"] for err in service.processing_errors)


def test_handle_missing_material(mock_parsed_dxf_data_basic):
    """测试处理缺失材料信息"""
    service = DataPreprocessorService(parsed_dxf_data=mock_parsed_dxf_data_basic)
    service._handle_missing_or_invalid_data()

    column_component = next(c for c in service.processed_data["bridge_components"] if c["component_id"] == "COLUMN_001")
    assert column_component["material"] is not None
    assert column_component["material"]["name"] == "未知" # Default material
    assert any(err["type"] == "DataWarning" and "COLUMN_001" in err["message"] and "缺少材料信息" in err["message"] for err in service.processing_errors)

def test_calculate_derived_geometry_properties_line_length(mock_parsed_dxf_data_basic):
    """测试计算LINE长度 (当原始长度缺失或需要重新计算时)"""
    data = copy.deepcopy(mock_parsed_dxf_data_basic)
    # 移除原始长度，强制重新计算
    del data["bridge_components"][0]["geometry_info"][0]["length"]
    data["metadata"]["units"] = 6 # Meters, so no unit conversion factor initially

    service = DataPreprocessorService(parsed_dxf_data=data)
    # 先进行单位转换（即使是米到米，确保流程正确）
    service._convert_units(dxf_unit_code=6, target_unit_name="meters")
    # 然后调用专业处理，其中包含几何属性计算
    service._calculate_derived_geometry_properties(service.processed_data["bridge_components"][0])

    beam_geom = service.processed_data["bridge_components"][0]["geometry_info"][0]
    # 原始坐标是 [0,0,0] to [10000,0,0]。如果单位是米，长度就是10000m
    # 之前fixture中length是10000，单位是mm。
    # 如果数据中原始坐标是10000mm，转换到米后是10m。
    # 在这个测试中，我们假设原始坐标已经是米，长度也应该是米。
    # mock_parsed_dxf_data_basic 里的坐标是 [0,0,0] to [10000,0,0]
    # 如果单位是米(6)，则长度是10000.0
    # 如果单位是毫米(4)，转为米后，坐标[0,0,0] to [10,0,0]，长度10.0

    # Let's re-evaluate the test setup for clarity.
    # We want to test if _calculate_derived_geometry_properties correctly calculates length
    # AFTER unit conversion.

    data_mm = copy.deepcopy(mock_parsed_dxf_data_basic) # units = 4 (mm)
    del data_mm["bridge_components"][0]["geometry_info"][0]["length"] # Remove pre-calculated length

    service_mm = DataPreprocessorService(parsed_dxf_data=data_mm)
    service_mm._convert_units(dxf_unit_code=4, target_unit_name="meters")
    # Now coords are in meters: [0,0,0] to [10,0,0]

    target_component = service_mm.processed_data["bridge_components"][0]
    service_mm._calculate_derived_geometry_properties(target_component)

    beam_geom_mm = target_component["geometry_info"][0]
    assert beam_geom_mm["length"] == pytest.approx(10.0)


def test_calculate_polyline_length(mock_parsed_dxf_data_with_duplicates_and_issues):
    """测试计算POLYLINE长度"""
    data = copy.deepcopy(mock_parsed_dxf_data_with_duplicates_and_issues) # units = 4 (mm)
    service = DataPreprocessorService(parsed_dxf_data=data)
    service._convert_units(dxf_unit_code=4, target_unit_name="meters")

    polyline_comp = next(c for c in service.processed_data["bridge_components"] if c["component_id"] == "POLY_001")
    # Original polyline coords in mm: [[0,0,0], [2000,0,0], [2000,1000,0], [0,1000,0]]
    # Converted to meters: [[0,0,0], [2,0,0], [2,1,0], [0,1,0]]
    # Lengths: 2m + 1m + 2m = 5m. (If closed, +1m back to origin, but length is usually open perimeter or sum of segments)
    # The current _calculate_derived_geometry_properties sums segments: (0,0,0)-(2,0,0) is 2. (2,0,0)-(2,1,0) is 1. (2,1,0)-(0,1,0) is 2. Total = 5.

    service._calculate_derived_geometry_properties(polyline_comp)
    geom_info = polyline_comp["geometry_info"][0]
    assert geom_info["length"] == pytest.approx(5.0)


def test_validate_component_reasonableness_zero_length(mock_parsed_dxf_data_with_duplicates_and_issues):
    """测试对零长度构件的合理性验证"""
    service = DataPreprocessorService(parsed_dxf_data=mock_parsed_dxf_data_with_duplicates_and_issues)
    # units are mm (4). Zero length is still zero in meters.
    service._convert_units(dxf_unit_code=4, target_unit_name="meters")

    zero_len_comp = next(c for c in service.processed_data["bridge_components"] if c["component_id"] == "ZERO_LEN_LINE_001")
    service._validate_component_reasonableness(zero_len_comp)

    assert any(
        err["type"] == "ReasonablenessWarning" and
        "ZERO_LEN_LINE_001" in err["message"] and
        "非常小" in err["message"]
        for err in service.processing_errors
    )

def test_assess_data_quality_basic_score(mock_parsed_dxf_data_basic):
    """测试基本的数据质量评分"""
    service = DataPreprocessorService(parsed_dxf_data=mock_parsed_dxf_data_basic)
    # Need to run other steps first as they might generate processing_errors
    service._clean_and_standardize_data() # Will add warning for missing material for COLUMN_001
    service._perform_bridge_specific_processing()
    service._assess_data_quality()

    report = service.get_quality_report()
    assert report["overall_score"] < 100.0 # Should be less due to missing material warning
    assert report["overall_score"] > 0.0
    assert len(report["issues"]) > 0
    assert any("DQ-COMP-002" in issue["code"] for issue in report["issues"]) # Missing material for COLUMN_001


def test_assess_data_quality_with_multiple_issues(mock_parsed_dxf_data_with_duplicates_and_issues):
    """测试包含多种问题的数据的质量评估"""
    service = DataPreprocessorService(parsed_dxf_data=mock_parsed_dxf_data_with_duplicates_and_issues)
    # Full processing pipeline
    service.process() # This will call all internal methods including _assess_data_quality

    report = service.get_quality_report()
    assert report["overall_score"] < 80 # Expect significant deductions

    issues_codes = [issue["code"] for issue in report["issues"]]
    # PROC-DATACLEANING (duplicate removed)
    # PROC-DATAWARNING (no component_id for UNKNOWN_COMP)
    # PROC-REASONABLENESSWARNING (ZERO_LEN_LINE_001) - this is a processing_error
    # DQ-COMP-001 (UNKNOWN_COMP type is UNKNOWN_FROM_TEST)
    # DQ-GEOM-004 (ZERO_LEN_LINE_001 has zero length) - this is a DQ issue

    assert "PROC-DATACLEANING" in issues_codes
    assert "PROC-DATAWARNING" in issues_codes # For no ID component
    assert "DQ-COMP-001" in issues_codes # For unknown type
    # The ReasonablenessWarning from _validate_component_reasonableness is a processing_error
    assert any(issue["code"] == "PROC-REASONABLENESSWARNING" and "ZERO_LEN_LINE_001" in issue["message"] for issue in report["issues"])
    # The DQ-GEOM-004 from _assess_data_quality for zero length
    assert "DQ-GEOM-004" in issues_codes


    assert report["statistics"]["total_components_raw"] == 6
    assert report["statistics"]["total_components_processed"] == 5 # after duplicate removal
    assert report["statistics"]["component_type_distribution"]["BEAM"] == 1
    assert report["statistics"]["component_type_distribution"]["COLUMN"] == 1
    assert report["statistics"]["component_type_distribution"]["UNKNOWN_FROM_TEST"] == 1
    assert report["statistics"]["material_distribution"]["混凝土"] > 0


def test_standardize_output_format(mock_parsed_dxf_data_basic):
    """测试输出格式标准化"""
    service = DataPreprocessorService(parsed_dxf_data=mock_parsed_dxf_data_basic)
    service._standardize_output_format()

    proc_info = service.processed_data.get("processing_info")
    assert proc_info is not None
    assert proc_info["status"] == "Successfully Preprocessed"
    assert "timestamp_utc" in proc_info
    assert service.processed_data["metadata"]["preprocessor_version"] == "0.1.0"
    assert service.processed_data["metadata"]["original_filename"] == "test_bridge.dxf"

# Further tests could include:
# - More complex unit conversion scenarios (e.g., inches to meters)
# - Specific error conditions during parsing that DataPreprocessorService needs to handle.
# - More detailed geometry calculation tests (Area for Polyline, Volume if thickness is present).
# - Testing of _infer_connections and _check_design_code_compliance once implemented.
# - Testing behavior with empty "bridge_components" list.
# - Testing with "errors" present in the input parsed_dxf_data.
