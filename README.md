# QClaw 九层 — KernelGOD v8 完整归档

**日期**: 2026-05-24（归档）  
**状态**: 九环全量测试通过 (7/7)  
**对齐度**: ~98%

---

## 系统概述

**QClaw 九层系统** 是一套自主进化的 AI Agent 框架 —— 一个**你的系统你做主**的智能体核心。

### 核心理念

```
⚖️ 架构宪法（不可违反）

LLM 是系统的"燃料"，不是"司机"。
系统=大脑（组织、决策、控制）
LLM=神经元（提供智能）

TaskPlanner → 调用LLM理解任务
DecisionCoordinator → 调用LLM选择工具
Executor → 调用LLM执行
Audit → 调用LLM审计

每个环节都用LLM的语义理解，但控制权在系统！

评估任何新模块时先问：控制权在系统还是LLM？
```

> **我的系统我做主。** LLM 提供智能（神经元），但组织、决策、控制的权力永远在系统手里。控制权在系统，不在 LLM。

### 三大核心原则

1. **先判断，再处理** — 收到任务后，先判断类型（简单/复杂/不确定），再决定怎么处理
2. **简单明确直接给结论** — 不要铺垫、不要废话，直击要点
3. **不确定就说不确定** — 不瞎编、不虚构、不猜测

### 主动原则（ProActive Agent）

参考清华 THUNLP 的 [ProActive Agent](https://github.com/thunlp/ProactiveAgent) 研究项目。

> AI 不只是响应指令的工具，而是能**主动感知环境、预测需求、在恰当时机主动提议**的协作者。

**三个主动维度：**
- **主动规划** — 看到目标，主动拆解步骤，不等用户问"该怎么做"
- **主动补全** — 发现遗漏或上下文不完整，主动补全，不让用户追问
- **主动优化** — 发现更好的方式，主动提出改进方案

**主动时机判断：**
- 用户明确给出任务 → 直接执行
- 目标清楚但路径模糊 → 主动规划后再执行
- 信息不足 → 先做能做的部分，同时主动提问
- 观察到用户可能的潜在需求 → 主动提醒

**避免过度主动：**
- 用户明确说了"别管"的事，不主动提
- 重复已达成的共识，不重复提醒
- 简单问题直接答，不"顺便"扯远

### 系统定位

**日抛型自进化人工智能系统：**
- **日抛型**：每天都会重置状态，从头开始学习和进化
- **自进化**：能够根据执行结果自动优化自己的决策策略
- **数据驱动进化**：每个任务完成后自动记录因果边、共现关系，形成技能知识图谱

---

## 九层架构（九环闭环）

系统按以下九层流程执行，每个环节都用 LLM 的语义理解，但控制权始终在系统：

### S1 路由 — 将用户输入路由到正确技能
将用户输入通过 5-Pass 评分（别名→关键词→标签→Pipeline→GNN）路由到正确的技能。覆盖 53 个技能、1018 个别名，路由对齐度 ~98%。

**强制规则**：收到任何任务消息后，必须先执行路由，再走后续流程，不可跳过。

### S2 系统控制器 — 大脑级流程控制、决策、校验、回退
系统出方案，自动写入 `_system_mandate.md`。3 种控制模式，LLM 审计。不允许跳过 S1-S4 直接执行，每个 LLM 调用都必须有 purpose + audit trail。

### S3 感知层 — 感知问题全貌、环境状态、工具准备
- 感知层理解用户输入的原始需求，分析真实意图
- 评估复杂程度（简单/中等/复杂/非常复杂）
- 任务分解为多个子步骤 + 识别依赖关系
- 预测步数 + 评估风险和困难点
- 工具准备：搜索用 anysearch_bridge（穿透 GFW），读网页用 x-reader

### S4 校验层 — 验证方案、质量评估、工具合法性校验
动态 VerificationLoop 校验方案，≤2 次重试，不过换方案。质量评估+工具合法性校验，确保每一步都安全可审计。

### S5 执行桥 — 编排执行，CLI 优先
按方案执行，**CLI 优先**原则：
- 禁止 LLM 目测代码 — 任何代码修改前先进行语法检查
- CLI 输出 > LLM 猜测
- 超过 3 个推测 = 空转 → 立刻切 CLI，停止推理

### S6 三路沉淀 — 因果/共现/SQLite 三路写入 + 每日学习
每次完成任务后自动执行：
1. 写入 `causal_edges.json` / `co_occurrence.json`（数据驱动进化）
2. 写入当日 memory 文件
3. 自动后台触发 pipeline_tick.py（阻塞时间 < 10ms）

### S7 复盘 — PageRank 排序 + 社区发现 + 热路径缓存
基于累积的因果图和共现数据，计算每个技能的重要性（核心/边缘），自动按社区分组，加速热路径。

### S8 快照 — 每步执行快照，故障回滚
每步执行快照，故障时可回滚。可恢复、可审计，保证系统运行的连续性和安全性。

### S9 技能结晶 — 质检→查重→结晶→写入注册表
质检→查重→结晶→写入注册表。已完成 14 个 beta 技能一键晋升到 stable，当前注册表 54 个稳定技能。

---

## 运行规则（强制）

```
S1 路由 → S2 系统出方案 → S3 感知+准备 → S4 校验
→ S5 执行 → S6 三路沉淀 → S7 复盘 → S8 快照 → S9 结晶
```

- **S1-S4 不可跳过**
- **CLI 优先，禁止 LLM 目测**
- **Thinking 预算：** Context <50% 用 1500 tokens，50-70% 用 800，70-85% 用 300，>85% 关闭 thinking
- **搜索优先：** 外网搜索优先用 anysearch_bridge 穿透 GFW
- **完成任务后自动执行 S6-S9（pipeline_tick 自动触发）**

---

## 目录结构

```
qclaw九层/
├── scripts/          # KernelGOD 核心执行器
│   ├── sagent_hook.py        # S1 路由入口，5-Pass评分
│   ├── daily_learning.py    # S6 反思/共现/SQLite沉淀
│   └── gateway_bridge.js   # ClawViz↔Gateway 桥接
├── tools/           # 调试/运维工具
│   ├── _check_triggers.py  # 检查 registry trigger 类型
│   ├── _fix_triggers.py    # 修复 trigger list→string
│   ├── _fix_registry_ids.py  # 补全缺失 id 字段
│   ├── _register_skills.py # 批量注册新技能
│   └── _validate_skills.py # YAML frontmatter 验证
├── skills/          # 6 个 GitHub 蒸馏技能
│   ├── skill-pydantic-model/   # pydantic 20k stars
│   ├── skill-api-fastapi/      # FastAPI 75k stars
│   ├── skill-system-design/     # system-design-primer 280k stars
│   ├── skill-python-project/    # black 88k + Python 最佳实践
│   ├── skill-workflow-patterns/# Prefect 16k + DAG/重试
│   └── skill-db-migration/    # Alembic + ORM 迁移
├── config/          # 注册表 & 配置
│   └── skill-registry.json   # 54 skills / 1018 aliases
└── README.md        # 本文档
```

---

## 九层架构速查

| 层 | 名称 | 功能描述 | 对应文件 | 状态 |
|---|---|---|---|---|
| S1 | 路由 | 将用户输入路由到正确技能 | `sagent_hook.py` | ✅ stable |
| S2 | 系统控制器 | 大脑级流程控制、决策、校验、回退 | `_system_mandate.md` | ✅ stable |
| S3 | 感知层 | 感知问题全貌、环境状态、工具准备 | anysearch_bridge / x-reader | ✅ stable |
| S4 | 校验层 | 验证方案、质量评估、工具合法性校验 | `verification_loop.py` | ✅ stable |
| S5 | 执行桥 | 编排执行，CLI优先 | `execution_bridge.py` | ✅ stable |
| S6 | 三路沉淀 | 因果/共现/SQLite 三路写入 + 每日学习 | `daily_learning.py` | ✅ stable |
| S7 | 复盘 | PageRank 排序 + 社区发现 + 热路径缓存 | `pipeline_tick.py` | ✅ beta |
| S8 | 快照 | 每步执行快照，故障回滚 | `checkpoint.json` | ✅ alpha |
| S9 | 结晶 | 质检→查重→结晶→写入注册表 | `crystallize.py` | ✅ stable |

---

## 快速验证

```powershell
# S1 路由测试
$env:PYTHONIOENCODING="utf-8"
D:\openclaw\tools\python313\python.exe sagent_hook.py --route "创建用户注册API"

# S6 记录
D:\openclaw\tools\python313\python.exe scripts\daily_learning.py record "测试" "skill-api-fastapi"

# 查看 registry
D:\openclaw\tools\python313\python.exe -c "
import json
r=json.load(open('config/skill-registry.json','r',encoding='utf-8'))
from collections import Counter
c=Counter(x['status'] for x in r['skills'])
print(f'Total: {len(r[\"skills\"])} | stable={c[\"stable\"]} | beta={c.get(\"beta\",0)}')
"
```

---

## 已知问题

1. `kernelgod_live.py` 缺失 — 需重建（注入实时 Context）
2. `token_hook.py` 路径未找到 — 搜索 `scripts/` 目录
3. `handshake.py` ack_message() 时序已修复（2026-05-24 02:17）
4. `SystemMonitor` Windows 挂起已修复（同上）

---

## 组件健康

| 组件 | 端口/路径 | 状态 |
|---|---|---|
| Gateway (node) | 37777 | ✅ 运行中 |
| QClaw (Electron) | 28789 | ✅ |
| ClawViz | 18998 | ✅ encodingTest.ok |
| gateway_bridge | PID 3900 | ✅ schtasks 自启 |
| skills | 54 stable | ✅ |

---

## 集成点

| 组件 | 用途 |
|------|------|
| Gateway Bridge | 跨服务执行、控制API暴露、快照触发 |
| ClawViz WS (18998) | 实时面板、控制模式切换、链路追踪 |
| WorkBuddy mcp_chat | 备选执行引擎（CodeBuddy 编码） |
| M-Flow KG | 知识图谱沉淀、长期记忆（因果→图谱） |
| Obsidian sync | 复盘结果同步到笔记 |

---

## 依赖关系

| 依赖 | 说明 |
|------|------|
| S7 → S6 | 复盘依赖三路沉淀产生的因果图数据 |
| S4 → S6 | 校验结果应反馈到因果边 |
| S5 → S3 | 执行依赖感知层的工具准备 |
| S8 → S5 | 快照在执行前后创建 |
| S9 → S4 | 技能结晶需通过校验层质量评估 |

---

*归档时间: 2026-05-24 02:55 GMT+8*
*最后更新: 2026-05-26*
