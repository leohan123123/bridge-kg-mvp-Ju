# backend/app/tests/services/test_dxf_parser.py
import unittest
from pathlib import Path
from ..services.dxf_parser import DXFParserService, ComponentType, Material

# 测试数据所在的目录
TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
TEST_DXF_FILE = TEST_DATA_DIR / "test_bridge.dxf"

# 确保测试DXF文件存在
if not TEST_DXF_FILE.exists():
    # 如果文件不存在，尝试从 create_test_dxf.py 创建它
    # 这使得测试可以独立运行，即使之前没有手动生成文件
    try:
        from .create_test_dxf import create_sample_dxf_for_testing # 在同级目录下查找
        create_sample_dxf_for_testing(TEST_DXF_FILE)
        print(f"Test DXF file was missing, created it at: {TEST_DXF_FILE}")
    except ImportError:
        # 如果create_test_dxf不在同一目录，尝试从services目录导入
        # This fallback is likely redundant if the primary relative import '.create_test_dxf' is correct.
        # However, to fulfill the request of changing all 'backend.app...' paths, this specific one will be removed.
        # If '.create_test_dxf' fails, the error will propagate.
        # try:
        #     from backend.app.tests.services.create_test_dxf import create_sample_dxf_for_testing
        #     create_sample_dxf_for_testing(TEST_DXF_FILE)
        #     print(f"Test DXF file was missing, created it at: {TEST_DXF_FILE}")
        # except ImportError:
        raise FileNotFoundError(
            f"Test DXF file '{TEST_DXF_FILE}' not found and could not be auto-generated. "
                "Please run create_test_dxf.py first."
            )
    if not TEST_DXF_FILE.exists(): # 再次检查
        raise FileNotFoundError(f"Failed to create test DXF file at: {TEST_DXF_FILE}")


class TestDXFParserService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """在所有测试开始前运行一次，加载和解析DXF文件"""
        if not TEST_DXF_FILE.is_file():
            raise FileNotFoundError(f"Test DXF file not found: {TEST_DXF_FILE}")

        cls.parser_service = DXFParserService(TEST_DXF_FILE)
        cls.parsed_data = cls.parser_service.parse() # 解析一次，供所有测试用例使用

        # 打印一些解析摘要信息，帮助调试测试
        print(f"\n--- TestDXFParserService setUpClass ---")
        print(f"Parsed DXF: {TEST_DXF_FILE}")
        print(f"Metadata: {cls.parsed_data.get('metadata')}")
        print(f"Found {len(cls.parsed_data.get('layers', []))} layers.")
        print(f"Found {len(cls.parsed_data.get('blocks', []))} blocks.")
        print(f"Found {len(cls.parsed_data.get('modelspace_entities', []))} modelspace entities.")
        print(f"Identified {len(cls.parsed_data.get('bridge_components', []))} bridge components.")
        if cls.parsed_data.get('errors'):
            print(f"Parsing errors: {cls.parsed_data.get('errors')}")
        print(f"--- End setUpClass ---\n")


    def test_01_file_loading_and_metadata(self):
        """测试DXF文件是否正确加载并提取了元数据"""
        self.assertIsNotNone(self.parser_service.doc, "DXF document should be loaded.")
        self.assertEqual(self.parsed_data["metadata"]["filename"], "test_bridge.dxf")
        # ezdxf.enums.InsertUnits.Millimeters 的值是 4
        self.assertEqual(self.parsed_data["metadata"]["units"], 4, "DXF units should be Millimeters (4)")
        self.assertEqual(len(self.parsed_data["errors"]), 0, f"Should have no parsing errors initially: {self.parsed_data['errors']}")

    def test_02_layer_parsing(self):
        """测试图层是否被正确解析"""
        layers = self.parsed_data["layers"]
        expected_layers = ["BEAMS_CONCRETE", "COLUMNS_STEEL", "SLABS_CONCRETE", "TEXT_INFO", "GENERAL_METAL_ELEMENTS", "0", "Defpoints"] # Changed GENERAL_STEEL_PARTS to GENERAL_METAL_ELEMENTS
        # 注意: ezdxf会自动创建 "0" 和 "Defpoints" 图层 (如果它们在文件中不存在但被引用或标准需要)

        parsed_layer_names = [layer["name"] for layer in layers]
        print(f"Parsed layer names: {parsed_layer_names}")

        for name in expected_layers:
            self.assertIn(name, parsed_layer_names, f"Expected layer '{name}' not found in parsed layers.")

        # 检查特定图层的属性 (示例)
        beams_layer = next((l for l in layers if l["name"] == "BEAMS_CONCRETE"), None)
        self.assertIsNotNone(beams_layer)
        self.assertEqual(beams_layer["color"], 2) # 青色 ACI

    def test_03_block_parsing(self):
        """测试块定义是否被解析"""
        blocks = self.parsed_data["blocks"]
        # 默认会有一些内部块，如 *Model_Space, *Paper_Space
        # 我们创建了一个名为 "TestBlock" 的块
        parsed_block_names = [block["name"] for block in blocks]
        print(f"Parsed block names: {parsed_block_names}")
        self.assertIn("TestBlock", parsed_block_names, "Custom block 'TestBlock' not found.")

        test_block = next((b for b in blocks if b["name"] == "TestBlock"), None)
        self.assertIsNotNone(test_block)
        # TestBlock 包含一个LINE和一个CIRCLE
        # self.assertEqual(test_block["entity_count"], 2) # 取决于ezdxf如何计算，block_record是Layout
                                                       # len(block_record) 会给出实体数量

    def test_04_entity_parsing_counts(self):
        """测试模型空间实体的数量"""
        # 根据 create_test_dxf.py:
        # 1 LINE (beam)
        # 1 CIRCLE (column)
        # 1 CIRCLE (general steel part for material test)
        # 1 LWPOLYLINE (slab)
        # 1 TEXT
        # 1 INSERT (TestBlock)
        # Total = 6 entities
        self.assertEqual(len(self.parsed_data["modelspace_entities"]), 6)

    def test_05_bridge_component_identification(self):
        """测试桥梁构件是否按规则被正确识别"""
        components = self.parsed_data["bridge_components"]

        # 预期识别的构件：
        # 1 Beam from BEAMS_CONCRETE layer (LINE)
        # 1 Column from COLUMNS_STEEL layer (CIRCLE)
        # 1 Slab from SLABS_CONCRETE layer (LWPOLYLINE)
        # Total = 3 components
        self.assertEqual(len(components), 3, f"Expected 3 bridge components, but got {len(components)}")

        component_types = [comp["component_type"] for comp in components]
        self.assertIn(ComponentType.BEAM.value, component_types)
        self.assertIn(ComponentType.COLUMN.value, component_types)
        self.assertIn(ComponentType.SLAB.value, component_types)

    def test_06_beam_component_details(self):
        """测试梁构件的详细属性"""
        beam_components = [c for c in self.parsed_data["bridge_components"] if c["component_type"] == ComponentType.BEAM.value]
        self.assertEqual(len(beam_components), 1, "Should identify exactly one beam component.")
        beam = beam_components[0]

        self.assertEqual(beam["layer"], "BEAMS_CONCRETE")
        self.assertIsNotNone(beam["material"])
        self.assertEqual(beam["material"]["name"], "混凝土") # From LAYER_MATERIAL_RULES "CONCRETE"
        self.assertEqual(beam["material"]["grade"], "C30")

        self.assertEqual(len(beam["geometry_info"]), 1)
        geom = beam["geometry_info"][0]
        self.assertEqual(geom["primitive_type"], "LINE")
        self.assertAlmostEqual(geom["length"], 5000.0, places=1) # 长度计算

    def test_07_column_component_details(self):
        """测试柱构件的详细属性"""
        column_components = [c for c in self.parsed_data["bridge_components"] if c["component_type"] == ComponentType.COLUMN.value]
        self.assertEqual(len(column_components), 1, "Should identify exactly one column component.")
        column = column_components[0]

        self.assertEqual(column["layer"], "COLUMNS_STEEL")
        self.assertIsNotNone(column["material"])
        self.assertEqual(column["material"]["name"], "钢材") # From LAYER_MATERIAL_RULES "STEEL"
        self.assertEqual(column["material"]["grade"], "Q345")

        self.assertEqual(len(column["geometry_info"]), 1)
        geom = column["geometry_info"][0]
        self.assertEqual(geom["primitive_type"], "CIRCLE")
        self.assertAlmostEqual(geom["radius"], 300.0, places=1)
        # 检查原始DXF属性中的颜色是否为ByLayer (256)
        self.assertEqual(geom["raw_dxf_attributes"]["color"], 256)


    def test_08_slab_component_details(self):
        """测试板构件的详细属性"""
        slab_components = [c for c in self.parsed_data["bridge_components"] if c["component_type"] == ComponentType.SLAB.value]
        self.assertEqual(len(slab_components), 1, "Should identify exactly one slab component.")
        slab = slab_components[0]

        self.assertEqual(slab["layer"], "SLABS_CONCRETE")
        self.assertIsNotNone(slab["material"])
        self.assertEqual(slab["material"]["name"], "混凝土")

        self.assertEqual(len(slab["geometry_info"]), 1)
        geom = slab["geometry_info"][0]
        self.assertEqual(geom["primitive_type"], "LWPOLYLINE")
        self.assertEqual(len(geom["coordinates"]), 4) # 四个顶点

    def test_09_material_inference_by_color_for_non_component(self):
        """测试非构件实体是否可以通过颜色推断材料 (如果适用)"""
        # 我们在 test_bridge.dxf 中添加了一个在 "GENERAL_STEEL_PARTS" 图层上的圆，颜色为 ACI 1
        # 这个图层不应匹配任何构件类型规则
        # 但颜色 ACI 1 应该匹配 COLOR_MATERIAL_RULES 中的 "钢材 Q235"

        general_metal_entity_data = None # Renamed variable for clarity
        for entity_data in self.parsed_data["modelspace_entities"]:
            if entity_data["layer"] == "GENERAL_METAL_ELEMENTS" and entity_data["type"] == "CIRCLE": # Updated layer name
                # 确保不是被错误识别为柱的那个
                # 直接访问 entity_data 中的 "center"
                if "center" in entity_data and entity_data["center"][1] == -2000.0: # y = -2000 的那个圆
                     general_metal_entity_data = entity_data # Renamed variable
                     break

        self.assertIsNotNone(general_metal_entity_data, "Test entity on GENERAL_METAL_ELEMENTS not found.")

        # 这个实体不应该被识别为一个BridgeComponent
        component_ids_from_general_layer = [
            c["component_id"] for c in self.parsed_data["bridge_components"]
            if general_metal_entity_data["handle"] in c["component_id"] # Updated variable
        ]
        self.assertEqual(len(component_ids_from_general_layer), 0,
            "Entity on GENERAL_METAL_ELEMENTS should not be identified as a bridge component based on layer rules.") # Updated message

        # 我们可以直接测试 _get_material_from_entity 方法，但这需要实例化 DXFParserService
        # 或者检查该实体是否在解析时被正确赋予了材料信息（如果我们的逻辑支持的话）
        # 当前 _get_material_from_entity 是在 _identify_bridge_components 内部调用的
        # 所以，如果一个实体没有被识别为构件，它的材料可能没有被显式解析并存储。
        # 为了测试这个，我们可以修改 _identify_bridge_components 或添加一个专门的材料解析步骤。
        #
        # 另一种方法是，我们可以检查这个实体是否在 _extract_entity_data 时记录了颜色。
        self.assertEqual(general_metal_entity_data["color"], 1) # ACI color 1 (red) # Updated variable

        # 如果要测试材料推断，我们需要一个方法来获取特定实体的推断材料，
        # 或者让 _identify_bridge_components 也存储那些未形成构件但有材料信息的实体。
        # 目前的测试主要验证已识别构件的材料。
        #
        # 让我们在DXFParserService中添加一个辅助方法来获取实体的推断材料，以便测试
        # （或者，为了简单起见，我们可以在这里模拟调用）

        # 模拟调用材料推断 (更直接的测试需要修改 DXFParserService 或其实例)
        simulated_material = self.parser_service._get_material_from_entity(general_metal_entity_data) # Updated variable
        self.assertIsNotNone(simulated_material, "Material should be inferred for the general metal part.") # Updated message
        self.assertEqual(simulated_material.name, "钢材")
        self.assertEqual(simulated_material.grade, "Q235")


if __name__ == '__main__':
    # 运行测试
    # 可以通过命令行 python -m unittest backend/app/tests/services/test_dxf_parser.py
    # 或者在IDE中运行
    unittest.main(verbosity=2)
