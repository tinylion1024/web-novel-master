# Phase 6 – Draft Writing

**重要**：全程无需向用户确认，必须逐章创作直到完成

---

## 6.1 启动检测

1. 读取 `03-写作计划.json`
2. 读取 `writingMode` 字段，进入对应模式
3. 如有 `status: "in_progress"` → 从该章节继续
4. 如有 `status: "failed"` → 从第一个 failed 章节开始
5. 全部 `pending` → 从第 1 章开始

---

## 6.2 逐章创作流程（通用）

每章严格按以下步骤执行：

### Step 1: 写前分析

1. 读取 `03-写作计划.json` — 确定下一个待创作章节
2. **读取 `00-大纲.md`** — 提取：
   - 核心事件、爽点设计、承接上章、悬念钩子
   - 名场面类型、情绪弧线
   - 伏笔埋设与回收
3. **一致性检查**（非第1章）：
   - 读取上一章摘要，核对人物状态、能力值、关系进展
   - 检查待回收伏笔是否已埋下
4. 更新 JSON — `status` 设为 `"in_progress"`

### Step 2: 撰写

5. 创建章节文件 — 使用 [chapter-template.md](../guides/chapter-template.md)
6. **基于大纲创作** — 严格按核心事件和爽点设计
7. **撰写正文** — 每章 2000-3000 字
   - 前20%必须有即时爽点 → [chapter-guide.md](../guides/chapter-guide.md)
   - 情绪曲线：憋→爽节奏
   - 人物语气：对话符合性格
8. **字数检查** — `python scripts/check_chapter_wordcount.py <文件路径>`

### Step 3: 撰写后优化

9. **爽点验证** — 确认爽点到位
10. **深度润色** — → [chapter-guide.md](../guides/chapter-guide.md)
    - 爽感强化、情绪外放、节奏加快
    - 金句植入、人物语气检查
    - 每500字必须有情节推进
11. **字数检查** — 再次确认
12. **伏笔检查** — 确认回收逻辑完整

### Step 4: 收尾

13. **生成章节摘要** — 在 `00-大纲.md` 追加 200-300 字
    - 包含：人物状态变化、关键事件、已埋/已回收伏笔
14. **更新 JSON** — `status` 设为 `"completed"`，填入 `wordCount`

---

## 6.3 串行模式（serial）

主 Agent 逐章创作，全程不中断。

```
WHILE 03-写作计划.json 中存在 status != "completed" 的章节:
    执行「逐章创作流程」
    完成一章后，立即读取 JSON 认领下一章
所有章节完成 → 进入 Phase 7
```

**关键提醒**：不要使用 AskUserQuestion，不要停下来，直到所有章节完成。

---

## 6.4 子Agent并行模式（subagent-parallel）

主 Agent 将章节分成不重叠批次，每个批次派生一个子 Agent。

### 主 Agent 流程

```
1. 计算批次分配（每批 5-8 章）
2. 并行派生子 Agent
3. 所有子 Agent 完成后 → 进入 Phase 7
```

### 子 Agent Prompt 模板

```
你是一个网文批量创作 Agent。创作第 {start} 章到第 {end} 章。

项目路径: {projectPath}
网文类型: [类型]
金手指: [金手指]
核心爽点: [核心爽点]

严格按「逐章创作流程」执行（详见 Phase6_Full_Draft_Writing.md 第6.2节）

约束：
- 不要使用 AskUserQuestion
- 每章开始前必须读取大纲
- 字数必须达到 2000 字以上
- 负责的所有章节必须全部完成

完成后报告: 各章编号、字数、是否通过字数检查
```

**并发安全**：每个子 Agent 负责不重叠章节批次，无写入冲突。

---

## 6.5 Agent Teams 模式（agent-teams）

Claude Code 多 Agent 协作，通过 TeamCreate 创建。

### 主 Agent 流程

```
1. TeamCreate 创建写作团队
2. 派生 3-5 个团队成员
3. TaskCreate 为每章创建任务
4. 团队成员各自：
   - 从 TaskList 读取任务
   - TaskUpdate 认领任务
   - 执行「逐章创作流程」
   - TaskUpdate 标记完成
   - 回到 TaskList 认领下一个
5. 所有任务完成 → 关闭团队 → 进入 Phase 7
```

### 团队成员 Prompt

```
你是一个网文创作团队成员。创作分配给你的章节。

项目路径: {projectPath}
网文类型: [类型]
金手指: [金手指]

工作流程：
1. TaskList 读取任务
2. TaskUpdate 认领任务
3. 读取大纲确认章节规划
4. 执行「逐章创作流程」（详见 Phase6_Full_Draft_Writing.md 第6.2节）
5. TaskUpdate 标记完成
6. 回到 TaskList 认领下一个

约束：
- 不要使用 AskUserQuestion
- 字数必须达到 2000 字以上
- 通过 SendMessage 与团队成员协调
```

**并发安全**：通过 TaskList 所有权语义和 Agent 间通讯避免冲突。

---

## 6.6 完成进入下一阶段

所有章节创作完成 → 进入 **Phase 7: Polish & Pacing**
