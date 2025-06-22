# 桥梁工程知识图谱数据模型文档

本文档详细描述了用于桥梁工程知识图谱的Neo4j数据模型，包括节点类型、关系类型及其属性。

## 1. 概述

知识图谱旨在存储和管理桥梁工程项目相关的各种信息，包括桥梁本身、其组成构件、所用材料以及遵循的设计和施工标准。通过图结构，可以方便地查询和分析这些实体之间的复杂关系。

## 2. 节点类型

知识图谱包含以下主要的节点类型（标签）：

### 2.1. Bridge (桥梁)

代表一个具体的桥梁工程项目。

*   **标签**: `Bridge`
*   **Pydantic模型**: `backend.app.models.graph_models.BridgeModel`
*   **核心属性**:
    *   `id` (String, 唯一标识符, UUID): 节点的唯一ID，由系统自动生成。
    *   `name` (String, 必需): 桥梁的名称，例如 "长江大桥"。
*   **特定属性**:
    *   `location` (String, 可选): 桥梁所在的地理位置，例如 "武汉市"。
    *   `construction_date` (String, 可选): 桥梁的建造日期 (建议格式: "YYYY-MM-DD")。
    *   `bridge_type` (String, 可选): 桥梁的结构类型，例如 "梁桥", "拱桥", "斜拉桥", "悬索桥"。
    *   `length_meters` (Float, 可选): 桥梁的总长度（单位：米）。
    *   `span_count` (Integer, 可选): 桥梁的跨数。
*   **通用附加属性**:
    *   `additional_props` (Map<String, Any>, 可选): 一个键值对映射，用于存储其他未在上面明确列出的自定义属性。例如: `{"designer": "某设计院", "main_span_meters": 1280}`。

### 2.2. Component (构件)

代表桥梁的一个组成部分或构件。

*   **标签**: `Component`
*   **Pydantic模型**: `backend.app.models.graph_models.ComponentModel`
*   **核心属性**:
    *   `id` (String, 唯一标识符, UUID): 节点的唯一ID。
    *   `name` (String, 必需): 构件的名称或编号，例如 "P1桥墩", "主缆A段"。
*   **特定属性**:
    *   `component_type` (String, 可选): 构件的类型，例如 "桥墩", "主梁", "桥面板", "吊索", "支座"。
*   **通用附加属性**:
    *   `additional_props` (Map<String, Any>, 可选): 其他自定义属性。例如: `{"height_meters": 25, "cross_section": "圆形", "drawing_id": "DWG-003"}`。

### 2.3. Material (材料)

代表用于制造构件的工程材料。

*   **标签**: `Material`
*   **Pydantic模型**: `backend.app.models.graph_models.MaterialModel`
*   **核心属性**:
    *   `id` (String, 唯一标识符, UUID): 节点的唯一ID。
    *   `name` (String, 必需): 材料的名称，例如 "C50混凝土", "Q345钢"。
*   **特定属性**:
    *   `material_type` (String, 可选): 材料的宏观类型，例如 "混凝土", "钢材", "复合材料", "沥青"。
    *   `strength_grade` (String, 可选): 材料的强度等级或牌号，例如 "C50", "Q345B"。
    *   `density_kg_m3` (Float, 可选): 材料的密度（单位：kg/m³）。
*   **通用附加属性**:
    *   `additional_props` (Map<String, Any>, 可选): 其他自定义属性。例如: `{"elastic_modulus_gpa": 200, "poisson_ratio": 0.3}`。

### 2.4. Standard (标准)

代表桥梁工程中涉及的设计规范、施工标准、材料标准或测试方法。

*   **标签**: `Standard`
*   **Pydantic模型**: `backend.app.models.graph_models.StandardModel`
*   **核心属性**:
    *   `id` (String, 唯一标识符, UUID): 节点的唯一ID。
    *   `name` (String, 必需): 标准的名称，例如 "公路桥涵设计通用规范"。
*   **特定属性**:
    *   `standard_code` (String, 可选): 标准的官方编号，例如 "JTG D60-2015"。
    *   `description` (String, 可选): 对标准的简要描述。
    *   `document_url` (String, 可选): 相关标准文档的URL链接 (如果可用)。
    *   `category` (String, 可选): 标准的分类，例如 "设计规范", "施工规范", "材料标准", "测试方法"。
*   **通用附加属性**:
    *   `additional_props` (Map<String, Any>, 可选): 其他自定义属性。例如: `{"issuing_authority": "中华人民共和国交通运输部", "publication_date": "2015-07-01"}`。

## 3. 关系类型

节点之间通过以下类型的关系连接：

### 3.1. HAS_COMPONENT (拥有构件)

*   **描述**: 表示一个桥梁 (`Bridge`) 包含/拥有一个构件 (`Component`)。
*   **方向**: `(Bridge) -[:HAS_COMPONENT]-> (Component)`
*   **属性**:
    *   `quantity` (Integer, 可选): 该类型构件的数量 (如果适用)。
    *   `installation_date` (String, 可选): 构件的安装日期。
    *   `additional_props` (Map<String, Any>, 可选): 其他关系特定属性。

### 3.2. MADE_OF (由...制成)

*   **描述**: 表示一个构件 (`Component`) 是由某种材料 (`Material`) 制成的。
*   **方向**: `(Component) -[:MADE_OF]-> (Material)`
*   **属性**:
    *   `volume_m3` (Float, 可选): 该构件所用此材料的体积（单位：立方米）。
    *   `coating_type` (String, 可选): 材料表面的涂层类型 (如果适用)。
    *   `additional_props` (Map<String, Any>, 可选): 其他关系特定属性。

### 3.3. CONNECTED_TO (连接到)

*   **描述**: 表示两个构件 (`Component`) 之间存在物理或逻辑上的连接。
*   **方向**: `(Component) -[:CONNECTED_TO]-> (Component)` (可以是有向的，表示连接的顺序或依赖性，也可以是无向的，具体取决于查询模式)
*   **属性**:
    *   `connection_type` (String, 可选): 连接的类型，例如 "焊接", "螺栓连接", "铆接", "铰接"。
    *   `relative_position` (String, 可选): 描述相对位置关系，例如 "上方", "相邻"。
    *   `additional_props` (Map<String, Any>, 可选): 其他关系特定属性。

### 3.4. FOLLOWS_SPEC (遵循标准)

*   **描述**: 表示一个桥梁 (`Bridge`) 或一个构件 (`Component`) 的设计、施工或材料等方面遵循了某个标准 (`Standard`)。
*   **方向**:
    *   `(Bridge) -[:FOLLOWS_SPEC]-> (Standard)`
    *   `(Component) -[:FOLLOWS_SPEC]-> (Standard)`
*   **属性**:
    *   `compliance_level` (String, 可选): 符合标准的程度，例如 "完全符合", "部分符合"。
    *   `specification_version` (String, 可选): 所遵循标准的具体版本号 (如果适用)。
    *   `additional_props` (Map<String, Any>, 可选): 其他关系特定属性。

## 4. 示例图片段 (Cypher风格)

```cypher
// 桥梁节点
(b1:Bridge {id: "uuid-bridge-1", name: "示例大桥", location: "某市", bridge_type: "斜拉桥"})

// 构件节点
(c1:Component {id: "uuid-comp-1", name: "主塔T1", component_type: "桥塔"})
(c2:Component {id: "uuid-comp-2", name: "主缆S1", component_type: "主缆"})
(c3:Component {id: "uuid-comp-3", name: "桥面D101", component_type: "桥面板"})

// 材料节点
(m1:Material {id: "uuid-mat-1", name: "C60混凝土", material_type: "混凝土", strength_grade: "C60"})
(m2:Material {id: "uuid-mat-2", name: "高强度钢丝", material_type: "钢材"})

// 标准节点
(s1:Standard {id: "uuid-std-1", name: "公路斜拉桥设计规范", standard_code: "JTG/T 3365-01-2020"})

// 关系示例
(b1)-[:HAS_COMPONENT {installation_date: "2023-01-15"}]->(c1)
(b1)-[:HAS_COMPONENT]->(c2)
(b1)-[:HAS_COMPONENT]->(c3)

(c1)-[:MADE_OF {volume_m3: 1200}]->(m1)  // 主塔由C60混凝土制成
(c2)-[:MADE_OF]->(m2)                   // 主缆由高强度钢丝制成
(c3)-[:MADE_OF]->(m1)                   // 桥面板也可能由C60混凝土制成

(c1)-[:CONNECTED_TO {connection_type: "固支"}]->(c3) // 桥塔与桥面连接
(c2)-[:CONNECTED_TO {connection_type: "锚固"}]->(c1) // 主缆锚固于桥塔

(b1)-[:FOLLOWS_SPEC]->(s1) // 整个桥梁遵循斜拉桥设计规范
(c2)-[:FOLLOWS_SPEC]->(s1) // 主缆的设计也遵循该规范
```

## 5. 未来扩展考虑

*   **更细化的构件层次**: 引入 `HAS_SUBCOMPONENT` 关系。
*   **空间数据**: 利用Neo4j的空间数据类型和索引。
*   **时间序列数据**: 为传感器读数、维护记录等引入 `Event` 或 `TimeSeriesData` 节点。
*   **版本控制**: 实现节点和关系的版本化管理。

本文档提供了当前知识图谱数据模型的基础。随着项目的发展，模型可能会进一步演化和完善。
```
