# 智能客服辅助系统

## 项目概述
本项目是一个基于AI技术的智能客服辅助系统，集成了文档管理、语义检索、知识图谱和多模态理解等功能，旨在提升客服工作效率和服务质量。

## 系统架构

### 1. 核心功能模块
#### 1.1 多模态理解 ✅
- CLIP模型集成
- 文本向量生成
- 图像向量生成
- 跨模态语义匹配

#### 1.2 文档管理 ✅
- 文档的CRUD操作
- 批量导入导出
- 文档版本控制
- 标签管理系统

#### 1.3 智能检索 ✅
- 语义相似度搜索
- 多模态检索支持
- 结果排序与过滤
- 相关度评分

#### 1.4 知识图谱
##### 1.4.1 关系管理 ✅
- 文档关系定义
- 关系CRUD操作
- 双向关系处理
- 关系属性管理

##### 1.4.2 图数据操作 ✅
- 批量关系处理
- 关系验证规则
- 关系类型兼容性
- 关系数量控制

##### 1.4.3 图分析功能 ✅
- 路径分析
- 关系推理
- 知识发现
- 图可视化

### 2. 技术架构
#### 2.1 后端服务 ✅
- FastAPI框架
- 异步处理
- RESTful API
- 模块化设计

#### 2.2 数据存储 ✅
- Neo4j图数据库
- 向量数据库
- 文件存储系统
- 缓存机制

#### 2.3 AI模型 ✅
- CLIP模型服务
- 向量计算服务
- 模型缓存优化
- CPU/GPU适配

## 项目状态

### 1. 已完成功能
#### 1.1 基础设施
- [x] 项目脚手架搭建
- [x] 开发环境配置
- [x] 依赖管理
- [x] 日志系统

#### 1.2 核心功能
- [x] CLIP模型集成
- [x] 文档基础操作
- [x] 向量检索
- [x] 关系管理
- [x] 批量操作
- [x] 验证规则
- [x] 图遍历功能
- [x] 路径查找
- [x] 关系推理

### 2. 进行中功能
#### 2.1 系统优化
- [ ] 性能监控
- [ ] 缓存策略
- [ ] 并发处理
- [ ] 分布式部署

#### 2.2 功能扩展
- [ ] 用户界面开发
- [ ] 权限管理系统
- [ ] 数据导入导出
- [ ] 报表统计

### 3. 已知问题
#### 3.1 性能问题
- 大规模关系查询性能优化
- 向量检索性能优化
- 内存使用优化
- 并发处理加强

#### 3.2 技术债务
- 完善错误处理机制
- 添加性能监控指标
- 增加自动化测试覆盖率
- 优化文档更新流程

## 最新更新（2024-01-15）
### 1. 功能完成
- ✅ 图像-文本匹配功能测试全部通过
- ✅ 批量操作和图遍历功能测试通过
- ✅ 关系验证功能测试全部通过
- ✅ 修复了文档创建和向量化问题

### 2. 测试覆盖
- ✅ 添加了完整的图像-文本匹配测试
- ✅ 完善了关系验证测试用例
- ✅ 增加了批量操作测试
- ✅ 补充了图遍历测试

### 3. 下一步计划
1. 性能优化
   - 优化大规模关系查询
   - 改进向量检索性能
   - 实现缓存机制
2. 系统改进
   - 实现分布式部署
   - 添加监控系统
   - 完善错误处理
3. 功能扩展
   - 开发Web界面
   - 实现权限管理
   - 添加数据导出功能

## 开发环境
### 1. 基础要求
- Python 3.9+
- Neo4j 4.4+
- CUDA 11.4+（可选）
- Docker 20.10+

### 2. 主要依赖
- FastAPI
- PyTorch
- Transformers
- Neo4j Python Driver
- ChromaDB

### 3. 开发工具
- VSCode/PyCharm
- Docker Desktop
- Neo4j Desktop
- Git

## 部署指南
### 1. 本地开发
1. 创建虚拟环境
2. 安装依赖
3. 配置环境变量
4. 启动数据库
5. 运行应用

### 2. Docker部署
1. 构建镜像
2. 配置网络
3. 启动容器
4. 验证服务

## API文档
### 1. 文档管理
#### 1.1 基础操作
- `POST /api/v1/documents/`: 创建新文档
- `GET /api/v1/documents/{doc_id}`: 获取文档
- `PUT /api/v1/documents/{doc_id}`: 更新文档
- `DELETE /api/v1/documents/{doc_id}`: 删除文档

#### 1.2 检索功能
- `POST /api/v1/documents/search/`: 语义相似度搜索
  - 参数：查询文本、结果数量限制
  - 返回：相似文档列表及相似度分数

### 2. 关系管理
#### 2.1 单一关系操作
- `POST /api/v1/documents/relations/`: 创建文档关系
  - 参数：源文档ID、目标文档ID、关系类型、关系属性
  - 返回：创建的关系信息

#### 2.2 批量关系操作
- `POST /api/v1/documents/relations/batch`: 批量创建关系
  - 参数：关系列表（每个关系包含源ID、目标ID、类型、属性）
  - 返回：创建结果

- `DELETE /api/v1/documents/relations/batch`: 批量删除关系
  - 参数：关系列表（源ID、目标ID、类型）
  - 返回：删除结果

### 3. 图遍历功能
#### 3.1 路径查找
- `GET /api/v1/documents/paths/`: 查找文档间路径
  - 参数：
    - start_id: 起始文档ID
    - end_id: 目标文档ID
    - relation_types: 关系类型列表（可选）
    - max_depth: 最大路径长度（默认5）
  - 返回：所有可能路径，包含节点和关系信息

#### 3.2 关系遍历
- `GET /api/v1/documents/{doc_id}/relations/traverse`: 遍历文档关系
  - 参数：
    - direction: 遍历方向（outgoing/incoming/all）
    - relation_types: 关系类型列表（可选）
    - max_depth: 最大遍历深度（默认3）
  - 返回：相关文档和关系列表

### 4. 使用示例
#### 4.1 创建文档关系
```python
# 创建两个文档之间的关系
relation_data = {
    "source_id": "doc1_id",
    "target_id": "doc2_id",
    "relation_type": "NEXT_STEP",
    "properties": {"order": 1}
}
response = requests.post(f"{BASE_URL}/documents/relations/", json=relation_data)
```

#### 4.2 查找文档路径
```python
# 查找两个文档之间的路径
params = {
    "start_id": "doc1_id",
    "end_id": "doc5_id",
    "relation_types": ["NEXT_STEP", "REFERENCES"],
    "max_depth": 5
}
response = requests.get(f"{BASE_URL}/documents/paths/", params=params)
```

#### 4.3 遍历文档关系
```python
# 遍历文档的出向关系
params = {
    "direction": "outgoing",
    "relation_types": ["NEXT_STEP"],
    "max_depth": 3
}
response = requests.get(f"{BASE_URL}/documents/{doc_id}/relations/traverse", params=params)
```

## 维护记录
### 2025-01-15
#### 完成功能
- 文档关系管理基础功能
- 批量操作和验证规则
- 图遍历基础实现

#### 修复问题
- 关系创建验证
- 批量操作错误处理
- 文档更新冲突

#### 待处理
- 图遍历功能优化
- 路径查找问题
- 查询性能改进

## 贡献指南
1. Fork项目
2. 创建特性分支
3. 提交变更
4. 发起Pull Request

## 版本规划
### v0.1.0（当前）
- 基础功能实现
- 核心模块开发
- 基本API支持

### v0.2.0（计划）
- 图分析完善
- 性能优化
- UI开发

### v1.0.0（远期）
- 完整功能集
- 生产环境就绪
- 全面测试覆盖


