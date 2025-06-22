# backend/app/services/dxf_parser.py
import ezdxf
from ezdxf.document import Drawing
from ezdxf.entitydb import EntityDB
from ezdxf.layouts import Modelspace
from typing import Optional, Dict, Any, List
from pathlib import Path

# 导入rich用于调试时美化输出 (可选)
from rich.console import Console
from rich.table import Table

console = Console()

class DXFParserService:
    """
    DXF文件解析服务
    负责从DXF文件中提取桥梁结构信息。
    """

    def __init__(self, file_path: str | Path):
        """
        初始化解析服务。

        Args:
            file_path (str | Path): DXF文件的路径。
        """
        self.file_path = Path(file_path)
        self.doc: Optional[Drawing] = None
        self.msp: Optional[Modelspace] = None
        self.entities: Optional[EntityDB] = None
        self.parsed_data: Dict[str, Any] = {
            "metadata": {},
            "layers": [],
            "blocks": [],
            "components": [],
            "errors": [],
        }

        if not self.file_path.exists() or not self.file_path.is_file():
            raise FileNotFoundError(f"DXF文件未找到: {self.file_path}")

        try:
            self.doc = ezdxf.readfile(self.file_path)
            self.msp = self.doc.modelspace()
            self.entities = self.doc.entitydb
            self.parsed_data["metadata"]["dxf_version"] = self.doc.dxfversion
            self.parsed_data["metadata"]["encoding"] = self.doc.encoding
            self.parsed_data["metadata"]["filename"] = self.file_path.name
            console.log(f"成功加载DXF文件: {self.file_path}, 版本: {self.doc.dxfversion}")
        except ezdxf.DXFStructureError as e:
            error_msg = f"解析DXF文件结构时出错: {e}"
            console.log(f"[bold red]{error_msg}[/bold red]")
            self.parsed_data["errors"].append({"type": "DXFStructureError", "message": error_msg})
            raise  # 重新抛出异常，让调用者知道加载失败
        except Exception as e:
            error_msg = f"加载DXF文件时发生未知错误: {e}"
            console.log(f"[bold red]{error_msg}[/bold red]")
            self.parsed_data["errors"].append({"type": "UnknownLoadingError", "message": error_msg})
            raise

    def parse(self) -> Dict[str, Any]:
        """
        执行DXF文件的完整解析过程。
        目前仅为骨架，后续将填充具体解析逻辑。

        Returns:
            Dict[str, Any]: 包含解析结果的字典。
        """
        if not self.doc or not self.msp:
            self.parsed_data["errors"].append({"type": "ParsingError", "message": "DXF文档未成功加载，无法解析。"})
            return self.parsed_data

# backend/app/services/dxf_parser.py
import ezdxf
from ezdxf.document import Drawing
from ezdxf.entitydb import EntityDB
from ezdxf.layouts import Modelspace
from typing import Optional, Dict, Any, List, Tuple as TypingTuple

from pathlib import Path
import math # 用于计算几何属性

# 导入rich用于调试时美化输出 (可选)
from rich.console import Console
from rich.table import Table

# 导入数据模型
from backend.app.models.bridge_component import BridgeComponent, ComponentType, Material, GeometryInfo

console = Console()

# 定义图层到构件类型的映射规则 (示例，需要根据实际情况调整)
# 规则可以更复杂，例如使用正则表达式匹配图层名称
LAYER_TO_COMPONENT_TYPE_RULES: Dict[str, ComponentType] = {
    "BEAM": ComponentType.BEAM,
    "COLUMN": ComponentType.COLUMN,
    "SLAB": ComponentType.SLAB,
    "FOUNDATION": ComponentType.FOUNDATION,
    "GIRDER": ComponentType.BEAM, # 另一种梁的叫法
    "PIER": ComponentType.PIER,
    "ABUTMENT": ComponentType.ABUTMENT,
    # ... 更多规则
}

# 定义从图层/颜色推断材料的规则 (非常简化)
# 实际项目中，材料信息可能来自文本、属性或更复杂的逻辑
LAYER_MATERIAL_RULES: Dict[str, Material] = {
    "CONCRETE": Material(name="混凝土", grade="C30"), # 默认等级
    "STEEL": Material(name="钢材", grade="Q345"),
}
COLOR_MATERIAL_RULES: Dict[int, Material] = {
    1: Material(name="钢材", grade="Q235"), # 假设颜色索引1代表某种钢材
    8: Material(name="混凝土", grade="C40"), # 假设颜色索引8代表某种混凝土
}


class DXFParserService:
    """
    DXF文件解析服务
    负责从DXF文件中提取桥梁结构信息。
    """

    def __init__(self, file_path: str | Path):
        """
        初始化解析服务。

        Args:
            file_path (str | Path): DXF文件的路径。
        """
        self.file_path = Path(file_path)
        self.doc: Optional[Drawing] = None
        self.msp: Optional[Modelspace] = None
        self.entities: Optional[EntityDB] = None
        self.parsed_data: Dict[str, Any] = {
            "metadata": {},
            "layers": [],
            "blocks": [],
            "modelspace_entities": [], # 存储从模型空间提取的原始实体信息
            "bridge_components": [], # 存储识别出的桥梁构件
            "errors": [],
        }

        if not self.file_path.exists() or not self.file_path.is_file():
            raise FileNotFoundError(f"DXF文件未找到: {self.file_path}")

        try:
            self.doc = ezdxf.readfile(self.file_path)
            self.msp = self.doc.modelspace()
            self.entities = self.doc.entitydb
            self.parsed_data["metadata"]["dxf_version"] = self.doc.dxfversion
            self.parsed_data["metadata"]["encoding"] = self.doc.encoding
            self.parsed_data["metadata"]["filename"] = self.file_path.name
            self.parsed_data["metadata"]["units"] = self.doc.header.get('$INSUNITS', 'Unitless') # 获取DXF文件的单位设置
            console.log(f"成功加载DXF文件: {self.file_path}, 版本: {self.doc.dxfversion}, 单位: {self.parsed_data['metadata']['units']}")
        except ezdxf.DXFStructureError as e:
            error_msg = f"解析DXF文件结构时出错: {e}"
            console.log(f"[bold red]{error_msg}[/bold red]")
            self.parsed_data["errors"].append({"type": "DXFStructureError", "message": error_msg})
            raise
        except Exception as e:
            error_msg = f"加载DXF文件时发生未知错误: {e}"
            console.log(f"[bold red]{error_msg}[/bold red]")
            self.parsed_data["errors"].append({"type": "UnknownLoadingError", "message": error_msg})
            raise

    def parse(self) -> Dict[str, Any]:
        """
        执行DXF文件的完整解析过程。

        Returns:
            Dict[str, Any]: 包含解析结果的字典。
        """
        if not self.doc or not self.msp:
            self.parsed_data["errors"].append({"type": "ParsingError", "message": "DXF文档未成功加载，无法解析。"})
            return self.parsed_data

        console.log("开始解析DXF文件内容...")
        self._parse_layers()
        self._parse_blocks()
        self._parse_modelspace_entities()
        self._identify_bridge_components() # 新增：调用桥梁构件识别方法

        console.log("DXF文件解析完成。")
        # 将解析出的构件转换为字典列表，方便API返回
        self.parsed_data["bridge_components"] = [comp.to_dict() for comp in self.parsed_data["bridge_components"]]
        return self.parsed_data

    def _parse_layers(self):
        """解析图层信息"""
        if not self.doc:
            return
        console.log("解析图层信息...")
        for layer in self.doc.layers:
            self.parsed_data["layers"].append({
                "name": layer.dxf.name,
                "color": layer.dxf.color, # ACI color index
                "true_color": layer.rgb, # RGB tuple if available
                "linetype": layer.dxf.linetype,
                "is_frozen": layer.is_frozen(),
                "is_off": layer.is_off(),
                "is_locked": layer.is_locked(),
                "description": layer.dxf.description if layer.dxf.is_supported("description") else None, # 更安全地获取图层描述
            })
        console.log(f"图层信息解析完成，共 {len(self.parsed_data['layers'])} 个图层。")

    def _parse_blocks(self):
        """解析块定义"""
        if not self.doc:
            return
        console.log("解析块定义...")
        for block_layout in self.doc.blocks: # block_layout is a BlockLayout object
            block_info = {
                "name": block_layout.name,
                "base_point": tuple(block_layout.base_point),
                "is_anonymous": getattr(block_layout.block_record, 'is_anonymous', False), # Use getattr for safety
                "is_xref": getattr(block_layout.block_record, 'is_xref', False),           # Use getattr for safety
                "entity_count": len(block_layout),
                "entities": []
            }
            # 可选择性地解析块内部的实体，但要注意这可能很复杂且数据量大
            # for entity in block_record:
            #     block_info["entities"].append(self._extract_entity_data(entity))
            self.parsed_data["blocks"].append(block_info)
        console.log(f"块定义解析完成，共 {len(self.parsed_data['blocks'])} 个块。")

    def _extract_entity_data(self, entity) -> Optional[Dict[str, Any]]:
        """
        从单个DXF实体中提取通用和特定类型的数据。
        这是一个辅助方法，用于被 _parse_modelspace_entities 和可能的 _parse_blocks 调用。
        """
        if entity is None:
            return None

        entity_type = entity.dxftype()
        common_attrs = {
            "handle": entity.dxf.handle,
            "layer": entity.dxf.layer,
            "color": entity.dxf.color, # ACI color
            "linetype": entity.dxf.linetype,
            "lineweight": entity.dxf.lineweight,
            "visible": entity.dxf.invisible == 0,
            "true_color": entity.rgb, # RGB tuple if available
            # 'xdata': entity.get_xdata_list() # 扩展数据，可能需要特定处理
        }

        specific_attrs = {"type": entity_type}
        try:
            if entity_type == "LINE":
                specific_attrs.update({
                    "start_point": tuple(entity.dxf.start),
                    "end_point": tuple(entity.dxf.end),
                })
            elif entity_type == "CIRCLE":
                specific_attrs.update({
                    "center": tuple(entity.dxf.center),
                    "radius": entity.dxf.radius,
                    "thickness": entity.dxf.thickness,
                })
            elif entity_type == "ARC":
                specific_attrs.update({
                    "center": tuple(entity.dxf.center),
                    "radius": entity.dxf.radius,
                    "start_angle": entity.dxf.start_angle,
                    "end_angle": entity.dxf.end_angle,
                    "thickness": entity.dxf.thickness,
                })
            elif entity_type in ["POLYLINE", "LWPOLYLINE"]:
                # LWPOLYLINE点是 (x, y, start_width, end_width, bulge)
                # POLYLINE 更复杂，有自己的顶点实体
                points = []
                if entity_type == "LWPOLYLINE":
                    for point in entity.get_points(format="xyseb"): # x, y, start_width, end_width, bulge
                        points.append(point)
                else: # POLYLINE
                    for vertex in entity.vertices:
                        points.append(tuple(vertex.dxf.location))
                specific_attrs.update({
                    "points": points,
                    "is_closed": entity.is_closed,
                    "elevation": entity.dxf.elevation if hasattr(entity.dxf, "elevation") else 0.0,
                    "thickness": entity.dxf.thickness if hasattr(entity.dxf, "thickness") else 0.0,
                })
            elif entity_type == "TEXT":
                specific_attrs.update({
                    "insert_point": tuple(entity.dxf.insert),
                    "text_string": entity.dxf.text,
                    "height": entity.dxf.height,
                    "rotation": entity.dxf.rotation, # in degrees
                    "style": entity.dxf.style,
                })
            elif entity_type == "MTEXT":
                specific_attrs.update({
                    "insert_point": tuple(entity.dxf.insert),
                    "text_string": entity.text, # MTEXT uses .text property
                    "height": entity.dxf.char_height,
                    "rotation": entity.dxf.rotation, # in degrees, or from direction vector
                    "attachment_point": entity.dxf.attachment_point,
                    "style": entity.dxf.style,
                })
            elif entity_type == "INSERT": # 块参照
                specific_attrs.update({
                    "block_name": entity.dxf.name,
                    "insert_point": tuple(entity.dxf.insert),
                    "x_scale": entity.dxf.xscale,
                    "y_scale": entity.dxf.yscale,
                    "z_scale": entity.dxf.zscale,
                    "rotation": entity.dxf.rotation,
                })
                # 属性 (ATTRIB) 通常附加到INSERT实体，需要特殊处理
                # if entity.has_attribs:
                #     specific_attrs["attributes"] = {attrib.dxf.tag: attrib.dxf.text for attrib in entity.attribs}

            # TODO: 添加对其他实体类型的支持，如 HATCH, DIMENSION, SPLINE, ELLIPSE 等
            else:
                # 对于未明确处理的类型，可以记录一个警告或跳过
                # console.log(f"  [yellow]未明确处理的实体类型: {entity_type}[/yellow]")
                return None # 或者只返回通用属性

            return {**common_attrs, **specific_attrs}
        except Exception as e:
            error_msg = f"提取实体 {entity.dxf.handle} ({entity_type}) 数据时出错: {e}"
            console.log(f"[bold red]{error_msg}[/bold red]")
            self.parsed_data["errors"].append({
                "type": "EntityExtractionError",
                "handle": entity.dxf.handle if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'handle') else 'N/A',
                "entity_type": entity_type,
                "message": error_msg
            })
            return None


    def _parse_modelspace_entities(self):
        """解析模型空间中的主要实体"""
        if not self.msp:
            return
        console.log("解析模型空间实体...")
        # 存储已解析的实体，后续可以用于构建 BridgeComponent
        self.parsed_data["modelspace_entities"] = []

        # 统计各种实体类型的数量
        entity_type_counts = {}

        for entity in self.msp:
            entity_data = self._extract_entity_data(entity)
            if entity_data:
                self.parsed_data["modelspace_entities"].append(entity_data)
                entity_type = entity_data["type"]
                entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1

        console.log(f"模型空间实体解析完成。共解析 {len(self.parsed_data['modelspace_entities'])} 个实体。")
        if entity_type_counts:
            console.log("实体类型统计:")
            for type_name, count in entity_type_counts.items():
                console.log(f"  - {type_name}: {count}")

    def _create_geometry_info_from_entity(self, entity_data: Dict[str, Any]) -> Optional[GeometryInfo]:
        """
        根据提取的实体数据创建 GeometryInfo 对象。
        """
        primitive_type = entity_data.get("type", "UNKNOWN")
        coords = None
        center = None
        radius = None
        length = None
        # 简单计算长度示例 (对于LINE)
        if primitive_type == "LINE":
            sp = entity_data.get("start_point")
            ep = entity_data.get("end_point")
            if sp and ep and len(sp) >= 2 and len(ep) >=2: # 确保至少有x,y坐标
                length = math.sqrt((ep[0] - sp[0])**2 + (ep[1] - sp[1])**2 + ((ep[2] - sp[2])**2 if len(sp) == 3 and len(ep) == 3 else 0))
                coords = [sp, ep]
        elif primitive_type == "CIRCLE":
            center = entity_data.get("center")
            radius = entity_data.get("radius")
        elif primitive_type in ["POLYLINE", "LWPOLYLINE"]:
            points_data = entity_data.get("points", [])
            if primitive_type == "LWPOLYLINE": # (x, y, start_width, end_width, bulge)
                coords = [(p[0], p[1], entity_data.get("elevation", 0.0)) for p in points_data]
            else: # POLYLINE, points are already (x,y,z)
                coords = points_data
            # TODO: 计算POLYLINE的长度和面积

        # 其他类型可以类似添加

        if not coords and not center and not radius: # 如果没有提取到关键几何信息，则可能不是我们关心的几何体
             # 对于TEXT, MTEXT等，它们有insert_point，但不直接构成构件的几何形状
            if primitive_type in ["TEXT", "MTEXT", "INSERT"]: # INSERT的几何由其内部实体定义
                return None # 或者创建一个表示标注点的GeometryInfo

        return GeometryInfo(
            primitive_type=primitive_type,
            coordinates=coords,
            center=center,
            radius=radius,
            length=length,
            # area, volume, dimensions 需要更复杂的计算或从属性中获取
            raw_dxf_attributes=entity_data # 存储原始提取数据
        )

    def _get_material_from_entity(self, entity_data: Dict[str, Any]) -> Optional[Material]:
        """尝试从图层名称或实体颜色推断材料"""
        layer_name = entity_data.get("layer", "").upper()
        color = entity_data.get("color") # ACI color

        # 优先基于图层名称
        for keyword, material in LAYER_MATERIAL_RULES.items():
            if keyword in layer_name:
                return material

        # 其次基于颜色
        if color and color in COLOR_MATERIAL_RULES:
            return COLOR_MATERIAL_RULES[color]

        return None


    def _identify_bridge_components(self):
        """
        识别桥梁构件。
        这是一个启发式过程，依赖于图层命名、块名称等约定。
        """
        console.log("开始识别桥梁构件...")
        identified_components: List[BridgeComponent] = []

        for entity_data in self.parsed_data.get("modelspace_entities", []):
            component_type = ComponentType.UNKNOWN
            layer_name = entity_data.get("layer", "").upper() # 转为大写以匹配规则

            # 1. 基于图层名称识别构件类型
            for keyword, c_type in LAYER_TO_COMPONENT_TYPE_RULES.items():
                if keyword in layer_name: # 使用 'in' 进行子字符串匹配，更灵活
                    component_type = c_type
                    break

            # 如果通过图层识别出了构件类型 (不是UNKNOWN)
            if component_type != ComponentType.UNKNOWN:
                geom_info = self._create_geometry_info_from_entity(entity_data)
                if geom_info: # 只有当实体能转换为有效几何信息时才创建构件
                    material = self._get_material_from_entity(entity_data)

                    # 使用实体句柄作为临时ID，确保唯一性
                    component_id = f"{component_type.name}_{entity_data.get('handle', 'NO_HANDLE')}"

                    # 尝试从文本实体中获取构件名称 (需要更复杂的邻近搜索逻辑)
                    # 此处仅为示例，实际应用中可能需要查找附近的TEXT/MTEXT实体
                    name = f"{component_type.value} (来自图层: {entity_data.get('layer')})"

                    component = BridgeComponent(
                        component_id=component_id,
                        component_type=component_type,
                        name=name,
                        layer=entity_data.get("layer"),
                        material=material,
                        geometry_info=[geom_info] # 一个实体对应一个构件 (初级阶段)
                    )
                    identified_components.append(component)

            # 2. TODO: 基于块参照(INSERT)识别构件
            # 如果 entity_data["type"] == "INSERT"，可以检查 entity_data["block_name"]
            # 并根据块名称查找预定义的构件库。

            # 3. TODO: 组合逻辑：将多个相关实体组合成一个构件
            # 例如，一个梁可能由多条线段或一个多段线表示，并附带文本标注。
            # 这需要更高级的几何分析和空间关系判断。

        self.parsed_data["bridge_components"] = identified_components
        console.log(f"桥梁构件识别完成。初步识别出 {len(identified_components)} 个构件。")
        # 调试输出一些识别到的构件
        # for comp in identified_components[:3]: # 只打印前3个
        #    console.print(comp.to_dict())


if __name__ == "__main__":
    # 创建一个虚拟的DXF文件用于测试 (实际使用时请替换为真实文件路径)
    # 注意: ezdxf不能直接创建一个空的、有效的DXF文件用于全面的测试，
    # 这里仅为演示模块的基本用法。
    # 通常你需要一个真实的DXF文件来进行测试。

    # 尝试创建一个简单的DXF文件 (如果不存在)
    temp_dxf_path = Path("temp_test.dxf")
    try:
        doc = ezdxf.new("R2018") # 创建一个新的DXF文档
        msp = doc.modelspace()
        msp.add_line((0, 0), (10, 0), dxfattribs={"layer": "Layer1"})
        msp.add_circle((0,0), radius=5, dxfattribs={"layer": "Layer2"})
        doc.saveas(temp_dxf_path)
        console.log(f"创建了临时测试DXF文件: {temp_dxf_path}")

        parser = DXFParserService(temp_dxf_path)
        result = parser.parse()

        # 使用Rich打印解析结果
        console.print("\n[bold green]DXF解析结果:[/bold green]")

        meta_table = Table(title="元数据")
        meta_table.add_column("属性", style="cyan")
        meta_table.add_column("值", style="magenta")
        for key, value in result.get("metadata", {}).items():
            meta_table.add_row(str(key), str(value))
        console.print(meta_table)

        if result.get("errors"):
            console.print("\n[bold red]解析错误:[/bold red]")
            for error in result["errors"]:
                console.print(f"- 类型: {error['type']}, 信息: {error['message']}")

    except ezdxf.DXFStructureError as e:
        console.log(f"[bold red]测试时DXF结构错误: {e}[/bold red]")
    except FileNotFoundError as e:
        console.log(f"[bold red]测试时文件未找到: {e}[/bold red]")
    except Exception as e:
        console.log(f"[bold red]测试时发生未知错误: {e}[/bold red]")
    finally:
        # 清理临时文件
        if temp_dxf_path.exists():
            temp_dxf_path.unlink()
            console.log(f"删除了临时测试DXF文件: {temp_dxf_path}")
