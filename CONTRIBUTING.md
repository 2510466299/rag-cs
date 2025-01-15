# 贡献指南

感谢您对智能客服辅助系统的关注！我们欢迎任何形式的贡献，包括但不限于：

- 报告问题
- 提交功能建议
- 改进文档
- 提交代码修复
- 添加新功能

## 开发流程

1. Fork 项目仓库
2. 创建功能分支
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 提交您的修改
   ```bash
   git commit -m "feat: add some feature"
   ```
4. 推送到您的仓库
   ```bash
   git push origin feature/your-feature-name
   ```
5. 创建 Pull Request

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat`: 新功能
- `fix`: 修复问题
- `docs`: 文档更新
- `style`: 代码格式修改
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

## 代码规范

- 遵循 PEP 8 规范
- 所有代码必须包含适当的注释
- 新功能必须包含测试用例
- 保持代码简洁可维护

## 测试要求

1. 运行现有测试
   ```bash
   python -m pytest
   ```
2. 添加新的测试用例
3. 确保所有测试通过
4. 保持测试覆盖率在 80% 以上

## 文档要求

- 更新 README.md（如果需要）
- 添加新功能的使用说明
- 更新 API 文档
- 添加必要的代码注释

## 分支策略

- `main`: 主分支，保持稳定
- `develop`: 开发分支
- `feature/*`: 功能分支
- `fix/*`: 修复分支
- `release/*`: 发布分支

## 发布流程

1. 从 `develop` 创建 `release` 分支
2. 进行必要的测试和修复
3. 合并到 `main` 分支
4. 创建版本标签
5. 更新版本文档

## 问题反馈

如果您发现任何问题，请：

1. 检查是否已存在相关 issue
2. 创建新的 issue，并提供：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息

## 联系方式

如有任何问题，请通过以下方式联系我们：

- Issue 系统
- 电子邮件：[待添加]
- 讨论区：[待添加] 