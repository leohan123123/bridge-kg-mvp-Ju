# backend/app/tests/services/create_test_dxf.py
import ezdxf
from ezdxf.enums import InsertUnits # 修正: InsUnits -> InsertUnits
from pathlib import Path

TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)

def create_sample_dxf_for_testing(filepath: Path):
    """
    创建一个用于单元测试的简单DXF文件。
    包含:
    - 图层: "BEAMS_CONCRETE", "COLUMNS_STEEL", "SLABS_CONCRETE", "TEXT_INFO"
    - 实体:
        - 一条线代表梁 (在 BEAMS_CONCRETE 图层)
        - 一个圆代表柱 (在 COLUMNS_STEEL 图层, 颜色为红色 ACI=1)
        - 一个LWPOLYLINE代表板 (在 SLABS_CONCRETE 图层)
        - 一段文字 (在 TEXT_INFO 图层)
    - 单位设置为毫米
    """
    doc = ezdxf.new("R2013", setup=True) # R2013是比较通用的版本
    doc.header['$INSUNITS'] = InsertUnits.Millimeters # 正确的枚举成员是 Millimeters (值为4)

    # 定义图层
    doc.layers.add(name="BEAMS_CONCRETE", color=2) # 青色
    doc.layers.add(name="COLUMNS_STEEL", color=1) # 红色
    doc.layers.add(name="SLABS_CONCRETE", color=3) # 绿色
    doc.layers.add(name="TEXT_INFO", color=7)    # 白色/黑色

    msp = doc.modelspace()

    # 梁 (LINE)
    msp.add_line(
        start=(0, 0, 0),
        end=(5000, 0, 0),
        dxfattribs={"layer": "BEAMS_CONCRETE"}
    )

    # 柱 (CIRCLE) - 注意：规则是LAYER_TO_COMPONENT_TYPE_RULES优先，然后才是颜色规则
    # 为了测试材料颜色规则，我们可以让一个实体的图层不触发构件类型识别，但颜色触发材料
    doc.layers.add(name="GENERAL_METAL_ELEMENTS", color=7) # 修改图层名
    msp.add_circle(
        center=(2500, -1000, 0),
        radius=300,
        dxfattribs={"layer": "COLUMNS_STEEL", "color": 256} # 256 表示 ByLayer, 所以会用COLUMNS_STEEL的颜色 (ACI 1)
    )
    # 添加一个不被识别为构件，但颜色能识别材料的圆
    msp.add_circle(
        center=(0, -2000, 0),
        radius=100,
        dxfattribs={"layer": "GENERAL_METAL_ELEMENTS", "color": 1} # ACI 1 -> Steel Q235 by COLOR_MATERIAL_RULES
    )


    # 板 (LWPOLYLINE - 矩形)
    points = [(0, 1000, 0), (5000, 1000, 0), (5000, 3000, 0), (0, 3000, 0)]
    msp.add_lwpolyline(
        points,
        close=True,
        dxfattribs={"layer": "SLABS_CONCRETE"}
    )

    # 文本信息
    msp.add_text(
        "Sample Beam B1",
        dxfattribs={
            "layer": "TEXT_INFO",
            "height": 200,
            "insert": (0, -500, 0)
        }
    )

    # 添加一个块定义和块参照，用于测试块解析
    block = doc.blocks.new(name="TestBlock")
    block.add_line((0,0), (100,100))
    block.add_circle((50,50), 50)
    msp.add_blockref("TestBlock", insert=(1000, -1000, 0), dxfattribs={"layer": "TEXT_INFO"})


    try:
        doc.saveas(filepath)
        print(f"测试DXF文件已创建: {filepath}")
    except Exception as e:
        print(f"创建测试DXF文件失败: {e}")

if __name__ == "__main__":
    sample_dxf_path = TEST_DATA_DIR / "test_bridge.dxf"
    create_sample_dxf_for_testing(sample_dxf_path)

    # 简单验证文件是否可读
    try:
        doc = ezdxf.readfile(sample_dxf_path)
        print(f"成功读取测试DXF文件 '{sample_dxf_path}'. 包含 {len(doc.modelspace())} 个实体。")
        print(f"文件单位: {doc.header.get('$INSUNITS', 'Not set')}")
        for layer in doc.layers:
            print(f"图层: {layer.dxf.name}, 颜色: {layer.dxf.color}, RGB: {layer.rgb}")
        for entity in doc.modelspace():
            print(f"实体: {entity.dxftype()}, Layer: {entity.dxf.layer}, Handle: {entity.dxf.handle}")
            if entity.dxftype() == "CIRCLE":
                print(f"  Center: {entity.dxf.center}, Radius: {entity.dxf.radius}, Color: {entity.dxf.color}, TrueColor: {entity.rgb}")
            if entity.dxftype() == "LINE":
                print(f"  Start: {entity.dxf.start}, End: {entity.dxf.end}")

    except Exception as e:
        print(f"读取或验证测试DXF文件失败: {e}")
