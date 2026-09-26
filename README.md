# tool-project-board-sync

> **本地智能体任务与 GitHub Projects v2 云端敏捷看板双向同步器**  
> Universal CLI Facade (UCFS v1.0) 标准实现 | 100% 离线自省 | GraphQL API v4 状态机无损同步

---

## 🌟 核心价值与实用性痛点解答

在使用多智能体协同（Pair Programming / Agent Clusters）解决复杂工程任务时，存在严重的人机协同视界割裂：
1. **进度黑盒痛点**：Agent 在本地高频生成 `tasks.json` 或更新 `PLANS.md`，但人类项目主管与利益相关方只在 GitHub 网页端的 Projects 看板查看项目进度。
2. **人工拖拽成本高**：如果每次任务状态变化都需要人去 GitHub 网页手动点击创建卡片、拖拽“In Progress”和“Done”，协同优势荡然无存。
3. **缺少轻量级数据泵**：传统方式需要配置重型第三方 SaaS 集成，存在权限过度开放与凭据泄露风险。

`tool-project-board-sync` 充当本地与云端看板的高性能轻量数据泵：
- **格式自适应解析**：自动读取 `tasks.json` 或 Markdown 检查清单（`- [ ]`, `- [/]`, `- [x]`, `- [!]`）。
- **GraphQL API v4 精确变更**：通过强类型 GraphQL Mutation 批量操作 GitHub Projects v2，设置标题、自定义状态字段。
- **离线沙箱模拟 (Simulation Mode)**：无 Token 或无网络时，自动以沙箱仿真模式运行并生成可视化的本地 Markdown 看板，单测 100% 离线解耦。

---

## ⚡ 极速开始 (Quick Start in 3 Seconds)

```bash
# 1. 环境校验
python main.py setup

# 2. 对当前目录任务清单进行看板同步模拟与解析
python main.py run

# 3. 运行离线单元测试
python main.py test

# 4. 核心健康自检
python main.py health

# 5. 清理缓存
python main.py clean
```

### 高级功能：实时云端同步与看板导出
```bash
# 查看本地任务在 Projects 看板视角下的列分布
python main.py status --target ./tasks.json

# 导出格式化 Kanban Markdown
python main.py sync --target ./tasks.json --export BOARD.md

# 实时推送到 GitHub Projects v2 (需提供 GITHUB_TOKEN)
python main.py sync --target ./tasks.json --project-id "PVT_kwDOBxxxx" --live
```

---

## 🛡️ 架构与不变式

- **独立职责**：专注本地任务状态机与 GitHub Projects v2 视图的数据同步，不修改任务实质内容。
- **离线确定性**：无外网网络或 Token 时优雅降级为离线仿真模式，保持系统高可用。

---

## 🚫 Non-Goals (明确非目标)

1. **不替代任务调度器**：本工具不决定任务的执行时序（时序由 Agent 决策或流水线指挥官裁决）。
2. **不删除云端已归档卡片**：本工具遵循只增量同步原则，绝不隐式物理删除用户的历史卡片。
3. **不越权修改源码**：除按需导出 Markdown 看板外，绝不修改用户源码。
