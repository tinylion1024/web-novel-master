---
name: web-novel-master
description: |
  面向中文网文创作的 AI 协作工作流。支持从选题、大纲到分章节校验的结构化创作，覆盖都市、玄幻、重生、言情等题材；提供节奏、人设与连续性检查，不保证作品热度或替代作者判断。
  当用户要求：写网文，写小说、创作故事、分章节写作、连续剧情时使用。
metadata:
  trigger: 网文创作、分章节故事、长篇小说创作、连续剧情
  source: 基于结构化创作与连续性校验实践设计
  supported_platforms:
    - claude_code
    - openclaw
---

# Web Novel Master: 结构化网文创作助手

## 创作检查原则

1. **冲突驱动** - 每章明确本章冲突、转折或推进点
2. **情绪节奏** - 为每章记录情绪目标，避免长期单一高压或平铺
3. **人物一致性** - 关键行为需符合人物动机，并回填人物档案
4. **连续性** - 记录伏笔、命名与章节状态，避免跨章矛盾

## 四种创作模式

| 模式 | Phase数 | 适用场景 |
|------|---------|---------|
| **Fast** | 5 | 爱好者，极简快速 |
| **Professional** | 8 | 作者，质量优先 |
| **Industrial** | 10 | 团队，流水线生产 |
| **Instant** | 1 | claude -n -p 非交互，一站式生成 |

---

## 核心流程

进入每个阶段时，先阅读对应的流程文档以获取详细执行指令。

### 模式选择

先根据用户需求选择创作模式。
→ 详见 [Mode_Selector.md](references/flows/Mode_Selector.md)

### 对应模式入口

用户选择模式后，进入对应入口文件执行初始化与后续流程：

- Fast → [Fast0_Initialization.md](references/flows/Fast/Fast0_Initialization.md)
- Professional → [Pro0_Initialization.md](references/flows/Pro/Pro0_Initialization.md)
- Industrial → [Ind0_Project_Initialize.md](references/flows/Ind/Ind0_Project_Initialize.md)
- Instant → [Instant0_One_Shot.md](references/flows/Instant/Instant0_One_Shot.md)

---

## 模式文件索引

### Fast 快速模式（5 Phase）

| Phase | 文件 | 核心职责 |
|-------|------|---------|
| 0 | Fast/Fast0_Initialization.md | 初始化 |
| 1 | Fast/Fast1_Idea_Clarify.md | 想法明确 |
| 2 | Fast/Fast2_Quick_Draft.md | 快速起草 |
| 3 | Fast/Fast3_Simple_Polish.md | 简单润色 |
| 4 | Fast/Fast4_Final_Validation.md | 最终校验 |

### Professional 专业模式（8 Phase）

| Phase | 文件 | 核心职责 |
|-------|------|---------|
| 0 | Pro/Pro0_Initialization.md | 初始化 |
| 1 | Pro/Pro1_Core_Clarify.md | 核心明确 |
| 2 | Pro/Pro2_World_Character_Setup.md | 世界观与人设 |
| 3 | Pro/Pro3_Outline_Planning.md | 大纲规划 |
| 4 | Pro/Pro4_Full_Draft_Writing.md | 正文撰写 |
| 5 | Pro/Pro5_Polish_Pacing.md | 润色节奏 |
| 6 | Pro/Pro6_Hook_Packaging.md | 钩子包装 |
| 7 | Pro/Pro7_Validation_Release.md | 校验发布 |

### Industrial 工业模式（10 Phase）

| Phase | 文件 | 核心职责 |
|-------|------|---------|
| 0 | Ind/Ind0_Project_Initialize.md | 项目初始化 |
| 1 | Ind/Ind1_Market_Research.md | 市场调研 |
| 2 | Ind/Ind2_Core_Positioning.md | 核心定位 |
| 3 | Ind/Ind3_World_Rule_Setup.md | 世界规则设定 |
| 4 | Ind/Ind4_Character_Standard.md | 人物标准化 |
| 5 | Ind/Ind5_Modular_Outline.md | 模块化大纲 |
| 6 | Ind/Ind6_Team_Writing.md | 团队写作 |
| 7 | Ind/Ind7_Unified_Polish.md | 统一润色 |
| 8 | Ind/Ind8_QC_Validation.md | QC校验 |
| 9 | Ind/Ind9_Release_Operation.md | 发布运营 |

### Instant 即刻模式（1 次生成）

| Phase | 文件 | 核心职责 |
|-------|------|---------|
| 0 | Instant/Instant0_One_Shot.md | 一站式生成 |

---

## 共享机制

偏好系统、写作计划系统、爆款网文速查表等跨阶段共享机制。
→ 详见 [Shared_Infrastructure.md](references/flows/Shared_Infrastructure.md)
