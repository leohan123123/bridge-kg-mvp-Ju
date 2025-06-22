# AGENTS.md
# 桥梁工程知识图谱平台 - AI代理说明

## 项目概述
智能建造知识图谱平台，用于处理桥梁设计文件（DXF）、构建知识图谱、提供AI问答和3D可视化。

## 技术栈
- 前端：React + Vite + Ant Design
- 后端：FastAPI + Python  
- 数据库：Neo4j
- AI：Ollama + 本地LLM
- 文件处理：ezdxf + PyMuPDF
- 3D展示：Three.js

## 项目结构
## 开发规范
- Python代码使用Type Hints
- React组件使用函数式组件和Hooks
- API接口遵循RESTful设计
- 所有函数需要详细注释
- 错误处理要完善

## 部署要求
- 使用Docker容器化部署
- 支持本地开发环境
- 配置文件使用环境变量

## Jules开发说明
本项目使用Jules AI代理进行开发，请遵循以下规范：

### 代码质量要求
- 所有Python函数必须包含类型注解
- React组件使用TypeScript
- 每个函数都要有详细的docstring注释
- 实现完善的错误处理机制

### 项目结构说明
- frontend/ 包含所有React前端代码
- backend/ 包含FastAPI后端服务
- 使用Docker进行容器化部署
- 环境配置通过.env文件管理

### 开发流程
1. 每个功能模块独立开发
2. 先创建基础框架再添加具体功能
3. 每个API接口都要有对应的前端页面
4. 所有数据操作都要经过验证

### 测试要求
- 后端API需要包含基本的测试用例
- 前端组件需要基本的渲染测试
- 数据库操作需要事务处理
- 文件上传需要格式验证