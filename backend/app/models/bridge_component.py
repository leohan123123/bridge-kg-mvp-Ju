# backend/app/models/bridge_component.py
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

class ComponentType(Enum):
    """
    桥梁构件类型枚举
    """
    BEAM = "梁"
    COLUMN = "柱"
    SLAB = "桥面板"
    FOUNDATION = "基础"
    CABLE = "拉索"
    BEARING = "支座"
    ABUTMENT = "桥台"
    PIER = "桥墩"
    HANDRAIL = "栏杆"
    OTHER = "其他"
    UNKNOWN = "未知"

class Material:
    """
    材料信息模型
    """
    def __init__(self, name: str, grade: Optional[str] = None, properties: Optional[Dict[str, Any]] = None):
        self.name = name  # 例如: "混凝土", "钢材"
        self.grade = grade # 例如: "C50", "Q345"
        self.properties = properties if properties else {} # 例如: {"弹性模量": "200GPa"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "grade": self.grade,
            "properties": self.properties,
        }

class GeometryInfo:
    """
    几何信息模型
    """
    def __init__(self,
                 primitive_type: str, # DXF 原始实体类型, e.g., "LINE", "CIRCLE", "LWPOLYLINE"
                 coordinates: Optional[List[Tuple[float, float, float]]] = None, # 顶点坐标列表
                 center: Optional[Tuple[float, float, float]] = None, # 圆心等
                 radius: Optional[float] = None, # 半径
                 length: Optional[float] = None, # 长度 (计算得出或直接获取)
                 area: Optional[float] = None,   # 面积 (计算得出或直接获取)
                 volume: Optional[float] = None, # 体积 (计算得出或直接获取)
                 dimensions: Optional[Dict[str, float]] = None, # 其他尺寸，如 {"width": 1.0, "height": 2.0}
                 raw_dxf_attributes: Optional[Dict[str, Any]] = None # 原始DXF属性
                ):
        self.primitive_type = primitive_type
        self.coordinates = coordinates if coordinates else []
        self.center = center
        self.radius = radius
        self.length = length
        self.area = area
        self.volume = volume
        self.dimensions = dimensions if dimensions else {}
        self.raw_dxf_attributes = raw_dxf_attributes if raw_dxf_attributes else {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primitive_type": self.primitive_type,
            "coordinates": self.coordinates,
            "center": self.center,
            "radius": self.radius,
            "length": self.length,
            "area": self.area,
            "volume": self.volume,
            "dimensions": self.dimensions,
            "raw_dxf_attributes": self.raw_dxf_attributes,
        }


class BridgeComponent:
    """
    桥梁构件数据模型
    """
    def __init__(self,
                 component_id: str, # 唯一标识符, 例如从DXF句柄生成或自定义
                 component_type: ComponentType = ComponentType.UNKNOWN,
                 name: Optional[str] = None, # 构件名称/编号, e.g., "主梁L1"
                 layer: Optional[str] = None, # 所在图层
                 material: Optional[Material] = None,
                 geometry_info: Optional[List[GeometryInfo]] = None, # 一个构件可能由多个几何实体组成
                 properties: Optional[Dict[str, Any]] = None, # 其他属性, e.g., {"重量": "10t"}
                 connections: Optional[List[str]] = None, # 连接的其他构件ID列表
                 design_standards: Optional[List[str]] = None # 设计标准引用
                ):
        self.component_id = component_id
        self.component_type = component_type
        self.name = name if name else component_id
        self.layer = layer
        self.material = material
        self.geometry_info = geometry_info if geometry_info else []
        self.properties = properties if properties else {}
        self.connections = connections if connections else [] # 初始化为空列表
        self.design_standards = design_standards if design_standards else [] # 初始化为空列表

    def add_geometry(self, geom: GeometryInfo):
        self.geometry_info.append(geom)

    def to_dict(self) -> Dict[str, Any]:
        """
        将构件信息转换为字典格式，方便JSON序列化。
        """
        return {
            "component_id": self.component_id,
            "component_type": self.component_type.value, # 使用枚举的值
            "name": self.name,
            "layer": self.layer,
            "material": self.material.to_dict() if self.material else None,
            "geometry_info": [geom.to_dict() for geom in self.geometry_info],
            "properties": self.properties,
            "connections": self.connections,
            "design_standards": self.design_standards,
        }

if __name__ == "__main__":
    # 示例用法
    from rich.console import Console
    console = Console()

    # 创建材料
    concrete_c50 = Material(name="混凝土", grade="C50", properties={"抗压强度": "50MPa"})
    steel_q345 = Material(name="钢材", grade="Q345", properties={"屈服强度": "345MPa"})

    # 创建几何信息
    line_geom = GeometryInfo(primitive_type="LINE", coordinates=[(0,0,0), (10,0,0)], length=10.0)
    circle_geom = GeometryInfo(primitive_type="CIRCLE", center=(0,0,0), radius=5.0, area=78.54)

    # 创建桥梁构件
    main_beam = BridgeComponent(
        component_id="BEAM_001",
        component_type=ComponentType.BEAM,
        name="主梁B1",
        layer="Bridge_Beams",
        material=concrete_c50,
        geometry_info=[line_geom],
        properties={"截面类型": "矩形", "宽度": 0.5, "高度": 1.0}
    )
    main_beam.add_geometry(GeometryInfo(primitive_type="LWPOLYLINE", coordinates=[(0,0,0),(1,1,0),(2,0,0)]))


    column = BridgeComponent(
        component_id="COL_001",
        component_type=ComponentType.COLUMN,
        name="桥墩P1-柱1",
        layer="Bridge_Columns",
        material=steel_q345,
        geometry_info=[circle_geom],
        properties={"截面类型": "圆形"}
    )
    column.connections.append("BEAM_001") # 添加连接关系

    console.print("示例桥梁构件数据模型:")
    console.print(main_beam.to_dict())
    console.print(column.to_dict())

    # 测试枚举
    assert ComponentType.BEAM.value == "梁"
    console.print(f"\nComponentType.SLAB: {ComponentType.SLAB}, Value: {ComponentType.SLAB.value}")
