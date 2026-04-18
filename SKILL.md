---
name: web-novel-master
description: |
  爆款网文创作助手。分章节创作引人入胜的爆款网文，支持都市爽文/玄幻修仙/穿越重生/甜宠言情等多种类型。每章2000-3000字，强调爽点驱动、名场面设计、金句记忆。
  当用户要求：写网文，写小说、创作故事、分章节写作、连续剧情时使用。
metadata:
  trigger: 爆款网文创作、分章节故事、长篇小说创作、网文写作
  source: 基于爆款网文最佳实践设计
  supported_platforms:
    - claude_code
    - openclaw
---

# Web Novel Master: 爆款网文创作助手

## 四大黄金法则

1. **爽点驱动** - 每章必须有爽点，读者追更是为了"爽"
2. **情绪波动** - 有憋有放，张弛有度，虐后必爽
3. **金句记忆** - 每章必须有让读者想截图的金句
4. **名场面** - 每3-5章必须有让人印象深刻的名场面

## 特性说明

- **10阶段流程**：从初始化到发布，结构清晰，逻辑连贯
- **名场面设计**：系统化设计每章的爽点名场面
- **金手指系统**：支持系统/重生/传承/异能等多种金手指
- **自动校验**：创作完成后自动检查字数、爽点密度、金句植入
- **并行写作**（可选）：支持子Agent并行写作和Agent Teams协作

## 核心流程（10阶段）

进入每个阶段时，先阅读对应的流程文档以获取详细执行指令。

| Phase | 名称 | 核心职责 |
|-------|------|---------|
| Phase 0 | Initialization | 初始化、偏好加载、中断续写检测 |
| Phase 1 | Market Research | 市场分析、套路速查、意向提取 |
| Phase 2 | Core Clarify | 类型、金手指、爽点、主角 |
| Phase 3 | World & Character Setup | 世界观、情感线、反派、名场面 |
| Phase 4 | Style Customization | 读者定位、章节数量、特殊要求 |
| Phase 5 | Outline Planning | 大纲生成、人物档案、写作计划 |
| Phase 6 | Full Draft Writing | 逐章创作、三种写作模式 |
| Phase 7 | Polish & Pacing | AI味清除、语言质量、节奏调整 |
| Phase 8 | Hook & Packaging | 标题优化、章节简介、连载钩子 |
| Phase 9 | Validation & Release | 自动校验、自动修复、完成报告 |

### Phase 0: Initialization

读取用户偏好，检测未完成项目（中断续写），展示个性化欢迎。
→ 详见 [Phase0_Initialization.md](references/flows/Phase0_Initialization.md)

### Phase 1-4: 需求收集

通过递进式问答收集创作需求：

- **Phase 1**: 市场调研、爆款套路速查、意向提取 → [Phase1_Market_Research.md](references/flows/Phase1_Market_Research.md)
- **Phase 2**: 类型、金手指、核心爽点、主角设定 → [Phase2_Core_Clarify.md](references/flows/Phase2_Core_Clarify.md)
- **Phase 3**: 世界观、情感线、反派设计、名场面规划 → [Phase3_World_Character_Setup.md](references/flows/Phase3_World_Character_Setup.md)
- **Phase 4**: 读者定位、章节数量、特殊要求 → [Phase4_Style_Customization.md](references/flows/Phase4_Style_Customization.md)

### Phase 5: Outline Planning

创建项目文件夹，生成大纲、人物档案和写作计划JSON，等待用户确认。
→ 详见 [Phase5_Outline_Planning.md](references/flows/Phase5_Outline_Planning.md)

### Phase 6: Full Draft Writing

**重要**：全程无需向用户确认，必须逐章创作直到完成。

根据用户选择的写作模式（串行/并行/Teams）逐章执行创作流程。
→ 详见 [Phase6_Full_Draft_Writing.md](references/flows/Phase6_Full_Draft_Writing.md)

**写作模式**：
- **逐章串行**（`serial`）：主 Agent 自己逐章写，全程无中断
- **子Agent并行**（`subagent-parallel`）：将章节分成批次，派生子 Agent 并行写作
- **Agent Teams**（`agent-teams`）：Claude Code 多 Agent 协作模式

### Phase 7: Polish & Pacing

深度润色，去除AI味，节奏调整。
→ 详见 [Phase7_Polish_Pacing.md](references/flows/Phase7_Polish_Pacing.md)

### Phase 8: Hook & Packaging

标题优化、章节简介撰写、连载钩子规划。
→ 详见 [Phase8_Hook_Packaging.md](references/flows/Phase8_Hook_Packaging.md)

### Phase 9: Validation & Release

全程无需用户介入，自动检查所有章节，不合格章节自动重写（最多3轮）。
→ 详见 [Phase9_Validation_Release.md](references/flows/Phase9_Validation_Release.md)

## 共享机制

偏好系统、写作计划系统、爆款网文速查表等跨阶段共享机制。
→ 详见 [Shared_Infrastructure.md](references/flows/Shared_Infrastructure.md)
