# backend/app/models/graph_models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid

# 通用基础节点模型，包含所有节点共有的属性
class BaseNode(BaseModel):
    """
    所有图节点模型的基础模型。
    自动生成一个唯一的 id (UUID) 如果没有提供。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="节点的唯一标识符")
    name: str = Field(..., description="节点的名称或标题")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点的其他自定义属性")

    class Config:
        schema_extra = {
            "example": {
                "id": "auto-generated-uuid",
                "name": "示例节点",
                "properties": {"key1": "value1", "key2": 123}
            }
        }

# 节点类型定义

class BridgeNode(BaseNode):
    """
    桥梁节点模型。
    """
    label: str = Field("Bridge", Literal=True, description="节点标签，固定为'Bridge'")
    location: Optional[str] = Field(None, description="桥梁所在的地理位置")
    construction_date: Optional[str] = Field(None, description="桥梁的建造日期")
    bridge_type: Optional[str] = Field(None, description="桥梁类型，例如梁桥、拱桥、斜拉桥等")
    length_meters: Optional[float] = Field(None, description="桥梁长度（米）")
    span_count: Optional[int] = Field(None, description="桥梁的跨数")

    class Config:
        schema_extra = {
            "example": {
                "id": "bridge-uuid-123",
                "name": "长江大桥",
                "label": "Bridge",
                "location": "武汉市",
                "construction_date": "1957-10-15",
                "bridge_type": "公路铁路两用桁架梁桥",
                "length_meters": 1670,
                "span_count": 10,
                "properties": {"designer": "某某设计院"}
            }
        }

class ComponentNode(BaseNode):
    """
    构件节点模型。
    """
    label: str = Field("Component", Literal=True, description="节点标签，固定为'Component'")
    component_type: Optional[str] = Field(None, description="构件类型，例如桥墩、主梁、吊索等")
    # material_id: Optional[str] = Field(None, description="构件所用材料的ID (未来可用于连接到MaterialNode)")
    # specification_id: Optional[str] = Field(None, description="构件遵循的设计规范ID (未来可用于连接到StandardNode)")

    class Config:
        schema_extra = {
            "example": {
                "id": "component-uuid-456",
                "name": "P1桥墩",
                "label": "Component",
                "component_type": "钢筋混凝土桥墩",
                "properties": {"height_meters": 25, "cross_section": "圆形"}
            }
        }

class MaterialNode(BaseNode):
    """
    材料节点模型。
    """
    label: str = Field("Material", Literal=True, description="节点标签，固定为'Material'")
    material_type: Optional[str] = Field(None, description="材料类型，例如钢材、混凝土、复合材料等")
    strength_grade: Optional[str] = Field(None, description="材料强度等级，例如C50混凝土, Q345钢")
    density_kg_m3: Optional[float] = Field(None, description="材料密度 (kg/m³)")

    class Config:
        schema_extra = {
            "example": {
                "id": "material-uuid-789",
                "name": "C50混凝土",
                "label": "Material",
                "material_type": "混凝土",
                "strength_grade": "C50",
                "density_kg_m3": 2500,
                "properties": {"elastic_modulus_gpa": 34.5}
            }
        }

class StandardNode(BaseNode):
    """
    标准或规范节点模型。
    """
    label: str = Field("Standard", Literal=True, description="节点标签，固定为'Standard'")
    standard_code: Optional[str] = Field(None, description="标准或规范的编号")
    description: Optional[str] = Field(None, description="标准的简要描述")
    document_url: Optional[str] = Field(None, description="相关标准文档的链接 (可选)")
    category: Optional[str] = Field(None, description="标准分类，如设计规范、施工规范、材料标准等")

    class Config:
        schema_extra = {
            "example": {
                "id": "standard-uuid-012",
                "name": "公路桥涵设计通用规范",
                "label": "Standard",
                "standard_code": "JTG D60-2015",
                "description": "规定了公路桥梁和涵洞设计的基本原则和要求。",
                "document_url": "http://example.com/standards/jtg_d60_2015.pdf",
                "category": "设计规范",
                "properties": {"issuing_authority": "中华人民共和国交通运输部"}
            }
        }

# 用于API请求和响应的模型

class NodeCreate(BaseModel):
    """
    创建节点时使用的模型。
    不包含id（由服务器生成）和label（由路径参数指定）。
    """
    name: str = Field(..., description="节点的名称或标题")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点的其他自定义属性")
    # 特定类型的属性，根据创建的节点类型动态添加或在API层处理
    # 例如，创建Bridge时，可以包含 location, construction_date 等
    # 为了通用性，这里只保留通用字段，特定字段通过 properties 传入

class NodeUpdate(BaseModel):
    """
    更新节点时使用的模型。所有字段都是可选的。
    """
    name: Optional[str] = Field(None, description="节点的新名称或标题")
    properties: Optional[Dict[str, Any]] = Field(None, description="要更新或添加的节点属性")
    # 特定类型的属性也应是可选的


# 关系模型 (概念性，实际创建通过服务层函数参数)
# Pydantic模型主要用于API交互时定义预期的关系数据结构

class RelationshipData(BaseModel):
    """
    用于API请求中定义关系的数据模型。
    """
    start_node_label: str = Field(..., description="起始节点的标签")
    start_node_id: str = Field(..., description="起始节点的ID")
    end_node_label: str = Field(..., description="结束节点的标签")
    end_node_id: str = Field(..., description="结束节点的ID")
    rel_type: str = Field(..., description="关系的类型 (例如 HAS_COMPONENT, MADE_OF)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系的可选属性")

    class Config:
        schema_extra = {
            "example": {
                "start_node_label": "Bridge",
                "start_node_id": "bridge-uuid-123",
                "end_node_label": "Component",
                "end_node_id": "component-uuid-456",
                "rel_type": "HAS_COMPONENT",
                "properties": {"connection_type": "刚性连接"}
            }
        }

# 用于从数据库返回节点数据的通用模型
class NodeResponse(BaseModel):
    """
    从数据库返回节点数据时的通用响应模型。
    """
    id: str
    labels: List[str]
    properties: Dict[str, Any]

    model_config = {
        "from_attributes": True  # Pydantic V2 equivalent of orm_mode = True
    }

# 用于从数据库返回关系数据的通用模型
class RelationshipResponse(BaseModel):
    """
    从数据库返回关系数据时的通用响应模型。
    """
    id: int # Neo4j 内部关系ID
    type: str
    start_node_id: str # 假设我们通过某种方式获取或构造
    end_node_id: str   # 假设我们通过某种方式获取或构造
    properties: Dict[str, Any]

    class Config:
        orm_mode = True


# 提示:
# 1. `Literal=True` for `label` fields in specific node types is not standard Pydantic.
#    The intention is to show that the label is fixed for that type.
#    In practice, the label is determined by the service/API endpoint.
#    A better way for Pydantic models is to not include `label` in the model itself,
#    or use it as a discriminator if using a Union of node types.
#    For this iteration, I'll remove `Literal=True` and the `label` field from specific node models.
#    The label will be handled by the GraphDatabaseService.

# Revised Node Models (removing fixed label and Literal=True)

class BridgeNodeProperties(BaseModel):
    location: Optional[str] = Field(None, description="桥梁所在的地理位置")
    construction_date: Optional[str] = Field(None, description="桥梁的建造日期")
    bridge_type: Optional[str] = Field(None, description="桥梁类型")
    length_meters: Optional[float] = Field(None, description="桥梁长度（米）")
    span_count: Optional[int] = Field(None, description="桥梁的跨数")
    # 可以添加其他桥梁特有属性

class BridgeNodeCreate(NodeCreate):
    name: str = Field(..., description="桥梁的名称")
    specific_properties: BridgeNodeProperties = Field(default_factory=BridgeNodeProperties)

class BridgeNodeResponse(BaseNode): # Inherits id, name, properties from BaseNode
    specific_properties: BridgeNodeProperties

# ---

class ComponentNodeProperties(BaseModel):
    component_type: Optional[str] = Field(None, description="构件类型")
    # material_id: Optional[str] = Field(None, description="材料ID")

class ComponentNodeCreate(NodeCreate):
    name: str = Field(..., description="构件的名称")
    specific_properties: ComponentNodeProperties = Field(default_factory=ComponentNodeProperties)

class ComponentNodeResponse(BaseNode):
    specific_properties: ComponentNodeProperties

# ---

class MaterialNodeProperties(BaseModel):
    material_type: Optional[str] = Field(None, description="材料类型")
    strength_grade: Optional[str] = Field(None, description="材料强度等级")
    density_kg_m3: Optional[float] = Field(None, description="材料密度 (kg/m³)")

class MaterialNodeCreate(NodeCreate):
    name: str = Field(..., description="材料的名称")
    specific_properties: MaterialNodeProperties = Field(default_factory=MaterialNodeProperties)

class MaterialNodeResponse(BaseNode):
    specific_properties: MaterialNodeProperties

# ---

class StandardNodeProperties(BaseModel):
    standard_code: Optional[str] = Field(None, description="标准编号")
    description: Optional[str] = Field(None, description="标准的简要描述")
    document_url: Optional[str] = Field(None, description="相关标准文档的链接")
    category: Optional[str] = Field(None, description="标准分类")

class StandardNodeCreate(NodeCreate):
    name: str = Field(..., description="标准的名称")
    specific_properties: StandardNodeProperties = Field(default_factory=StandardNodeProperties)

class StandardNodeResponse(BaseNode):
    specific_properties: StandardNodeProperties

# This revised structure separates generic node creation/update fields (name, generic properties)
# from type-specific properties. The `BaseNode` still provides `id`, `name`, `properties`.
# `NodeCreate` is for generic creation, and type-specific create models like `BridgeNodeCreate`
# embed their specific properties. Response models also follow this pattern.
# The `label` will be handled by the service layer based on the type of node being processed.
# The initial simpler models (BridgeNode, ComponentNode, etc. inheriting BaseNode and having a 'label' field)
# are also a valid approach, especially if the API endpoints are distinct for each node type.
# For now, I will proceed with the revised structure as it's a bit more flexible for the service layer.
# The `properties` field in `BaseNode` can store any additional, non-standardized attributes.
# The `specific_properties` in derived models handle the well-defined attributes for each node type.

# Let's simplify for now and revert to the initial structure where each node type has its own model
# and the label is implicitly defined by the model or handled at the service layer.
# The `label: str = Field("Bridge", Literal=True)` was problematic, so I'll remove `Literal=True`.
# The service layer will be responsible for using the correct label when creating nodes.

# Re-simplifying to the first approach for clarity in this step.
# The `label` field in Pydantic models here is more for documentation/typing,
# the actual Neo4j label assignment will be in the service.

del BridgeNodeProperties, BridgeNodeCreate, BridgeNodeResponse
del ComponentNodeProperties, ComponentNodeCreate, ComponentNodeResponse
del MaterialNodeProperties, MaterialNodeCreate, MaterialNodeResponse
del StandardNodeProperties, StandardNodeCreate, StandardNodeResponse

# Re-defining with the simpler structure for this step
# (label field will be used by service, not as a fixed Pydantic literal)

class Bridge(BaseNode): # Renamed from BridgeNode for brevity
    # id, name, properties inherited from BaseNode
    location: Optional[str] = Field(None, description="桥梁所在的地理位置")
    construction_date: Optional[str] = Field(None, description="桥梁的建造日期")
    bridge_type: Optional[str] = Field(None, description="桥梁类型")
    length_meters: Optional[float] = Field(None, description="桥梁长度（米）")
    span_count: Optional[int] = Field(None, description="桥梁的跨数")
    # Neo4j Label for this type will be "Bridge" (handled by service)

class Component(BaseNode):
    component_type: Optional[str] = Field(None, description="构件类型")
    # Neo4j Label for this type will be "Component"

class Material(BaseNode):
    material_type: Optional[str] = Field(None, description="材料类型")
    strength_grade: Optional[str] = Field(None, description="材料强度等级")
    density_kg_m3: Optional[float] = Field(None, description="材料密度 (kg/m³)")
    # Neo4j Label for this type will be "Material"

class Standard(BaseNode):
    standard_code: Optional[str] = Field(None, description="标准编号")
    description: Optional[str] = Field(None, description="标准的简要描述")
    document_url: Optional[str] = Field(None, description="相关标准文档的链接")
    category: Optional[str] = Field(None, description="标准分类")
    # Neo4j Label for this type will be "Standard"

# Generic models for API input (excluding id)
class NodeCreateRequest(BaseModel):
    name: str = Field(..., description="节点的名称")
    # Specific fields like 'location' for a Bridge will be part of the model passed to the API
    # This generic request can be part of a larger request model or used with type-specific models.
    # For simplicity, API endpoints will likely expect the full specific model (e.g., Bridge, Component).
    # So, the specific models (Bridge, Component, etc.) can serve for both creation (input) and response (output).
    # When used as input, 'id' would be ignored if provided, or generated.

# Example: A request to create a bridge might look like:
# POST /bridges/
# Body: Bridge model (id can be omitted or will be ignored/regenerated)

# Models for relationships will primarily be handled via parameters in service methods
# and the `RelationshipData` model for API input if a generic relationship endpoint is created.
# `NodeResponse` and `RelationshipResponse` are good for generic query results.

# Final check on structure for this step:
# - BaseNode: common fields (id, name, generic_properties dict)
# - Specific Node Models (Bridge, Component, Material, Standard): inherit BaseNode, add specific typed fields.
#   These models will be used for API request bodies (for creation/update) and response bodies.
#   The `id` field will be output-only for creation.
# - RelationshipData: for API input when creating relationships explicitly.
# - NodeResponse / RelationshipResponse: for generic query outputs.

# Let's ensure the specific node models are clear for API usage.
# The `properties` dict in BaseNode is for truly dynamic/additional key-value pairs.
# Well-known attributes should be first-class fields in the specific models.

# Re-adjusting BaseNode and specific models slightly:
# BaseNode will contain id.
# Specific models will contain name and other specific fields.
# A generic 'attributes' dict can be added if needed for extra non-typed properties.

class NodeModel(BaseModel): # Base for all our graph node Pydantic models
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="节点的唯一标识符 (通常由系统生成)")

class BridgeModel(NodeModel):
    name: str = Field(..., description="桥梁的名称")
    location: Optional[str] = Field(None, description="桥梁所在的地理位置")
    construction_date: Optional[str] = Field(None, description="桥梁的建造日期")
    bridge_type: Optional[str] = Field(None, description="桥梁类型")
    length_meters: Optional[float] = Field(None, description="桥梁长度（米）")
    span_count: Optional[int] = Field(None, description="桥梁的跨数")
    additional_props: Dict[str, Any] = Field(default_factory=dict, description="其他自定义属性")

    model_config = {
        "json_schema_extra": {
            "example_input": { # Example for creation (id might be omitted)
                "name": "金门大桥",
                "location": "旧金山",
                "bridge_type": "悬索桥",
                "length_meters": 2737,
                "additional_props": {"main_span_meters": 1280}
            },
            "example_output": { # Example for response
                "id": "generated-uuid-bridge",
                "name": "金门大桥",
                "location": "旧金山",
                "bridge_type": "悬索桥",
                "length_meters": 2737,
                "span_count": None,
                "construction_date": None,
                "additional_props": {"main_span_meters": 1280}
            }
        }
    }

class ComponentModel(NodeModel):
    name: str = Field(..., description="构件的名称")
    component_type: Optional[str] = Field(None, description="构件类型")
    additional_props: Dict[str, Any] = Field(default_factory=dict, description="其他自定义属性")

class MaterialModel(NodeModel):
    name: str = Field(..., description="材料的名称")
    material_type: Optional[str] = Field(None, description="材料类型")
    strength_grade: Optional[str] = Field(None, description="材料强度等级")
    density_kg_m3: Optional[float] = Field(None, description="材料密度 (kg/m³)")
    additional_props: Dict[str, Any] = Field(default_factory=dict, description="其他自定义属性")

class StandardModel(NodeModel):
    name: str = Field(..., description="标准的名称")
    standard_code: Optional[str] = Field(None, description="标准编号")
    description: Optional[str] = Field(None, description="标准的简要描述")
    document_url: Optional[str] = Field(None, description="相关标准文档的链接")
    category: Optional[str] = Field(None, description="标准分类")
    additional_props: Dict[str, Any] = Field(default_factory=dict, description="其他自定义属性")


# For creation, we might want models without `id` as it's server-generated.
class BridgeCreateSchema(BaseModel):
    name: str = Field(..., description="桥梁的名称")
    location: Optional[str] = Field(None, description="桥梁所在的地理位置")
    construction_date: Optional[str] = Field(None, description="桥梁的建造日期")
    bridge_type: Optional[str] = Field(None, description="桥梁类型")
    length_meters: Optional[float] = Field(None, description="桥梁长度（米）")
    span_count: Optional[int] = Field(None, description="桥梁的跨数")
    additional_props: Dict[str, Any] = Field(default_factory=dict, description="其他自定义属性")

class ComponentCreateSchema(BaseModel):
    name: str = Field(..., description="构件的名称")
    component_type: Optional[str] = Field(None, description="构件类型")
    additional_props: Dict[str, Any] = Field(default_factory=dict, description="其他自定义属性")

class MaterialCreateSchema(BaseModel):
    name: str = Field(..., description="材料的名称")
    material_type: Optional[str] = Field(None, description="材料类型")
    strength_grade: Optional[str] = Field(None, description="材料强度等级")
    density_kg_m3: Optional[float] = Field(None, description="材料密度 (kg/m³)")
    additional_props: Dict[str, Any] = Field(default_factory=dict, description="其他自定义属性")

class StandardCreateSchema(BaseModel):
    name: str = Field(..., description="标准的名称")
    standard_code: Optional[str] = Field(None, description="标准编号")
    description: Optional[str] = Field(None, description="标准的简要描述")
    document_url: Optional[str] = Field(None, description="相关标准文档的链接")
    category: Optional[str] = Field(None, description="标准分类")
    additional_props: Dict[str, Any] = Field(default_factory=dict, description="其他自定义属性")

# For updates, all fields should be optional.
class BridgeUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="桥梁的名称")
    location: Optional[str] = Field(None, description="桥梁所在的地理位置")
    construction_date: Optional[str] = Field(None, description="桥梁的建造日期")
    bridge_type: Optional[str] = Field(None, description="桥梁类型")
    length_meters: Optional[float] = Field(None, description="桥梁长度（米）")
    span_count: Optional[int] = Field(None, description="桥梁的跨数")
    additional_props: Optional[Dict[str, Any]] = Field(None, description="其他自定义属性")

class ComponentUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="构件的名称")
    component_type: Optional[str] = Field(None, description="构件类型")
    additional_props: Optional[Dict[str, Any]] = Field(None, description="其他自定义属性")

class MaterialUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="材料的名称")
    material_type: Optional[str] = Field(None, description="材料类型")
    strength_grade: Optional[str] = Field(None, description="材料强度等级")
    density_kg_m3: Optional[float] = Field(None, description="材料密度 (kg/m³)")
    additional_props: Optional[Dict[str, Any]] = Field(None, description="其他自定义属性")

class StandardUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="标准的名称")
    standard_code: Optional[str] = Field(None, description="标准编号")
    description: Optional[str] = Field(None, description="标准的简要描述")
    document_url: Optional[str] = Field(None, description="相关标准文档的链接")
    category: Optional[str] = Field(None, description="标准分类")
    additional_props: Optional[Dict[str, Any]] = Field(None, description="其他自定义属性")


# RelationshipData remains useful for explicit relationship creation API.
# NodeResponse and RelationshipResponse are good for generic results.
# This structure of Model (for DB representation/response) and Schema (for API input) is common.
# Let's stick to this for now.
# Note: `additional_props` allows flexibility. If certain properties become standard,
# they should be promoted to first-class fields in the Pydantic models.
# The `id` is generated by `default_factory=lambda: str(uuid.uuid4())` in `NodeModel`,
# which means it will always be present unless explicitly overridden.
# For creation via API, the `CreateSchema` models (which don't include `id`) are appropriate for request bodies.
# The service layer will then combine this with a generated `id` to create the full `Model` for DB storage.
# Response from GET/POST/PUT will typically be the full `Model` (e.g., `BridgeModel`).

# Final check of requirements for this step:
# - Node types: Bridge, Component, Material, Standard -> Done with `BridgeModel`, `ComponentModel`, etc.
# - Relationship types: HAS_COMPONENT, MADE_OF, CONNECTED_TO, FOLLOWS_SPEC -> Conceptual, `RelationshipData` for API.
# - Define node and relationship properties schema -> Done via Pydantic models and `additional_props`.

# The `NodeResponse` and `RelationshipResponse` are for generic Cypher query results.
# For specific CRUD, we'll use the typed models.
# I'll keep `NodeResponse` and `RelationshipResponse` as defined earlier for now.
# They are useful if we have an API endpoint that returns raw node/relationship data from a custom query.
# The `orm_mode = True` (now `from_attributes = True` in Pydantic V2) is useful if mapping directly from ORM-like objects.
# Neo4j driver returns `Record` objects, so we'll manually map them in the service layer.
# So `orm_mode` might not be strictly necessary here but doesn't hurt.
# Pydantic V1 uses `orm_mode = True`. Pydantic V2 uses `model_config = {"from_attributes": True}`.
# Assuming project uses Pydantic V1 based on current `config.py`.

# One final thought: using `NodeModel` as a base for `BridgeModel` etc. is good.
# For API input, `BridgeCreateSchema` etc. are good.
# For API output, `BridgeModel` etc. are good.
# This seems like a robust setup.
