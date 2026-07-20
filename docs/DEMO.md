# 快速演示

本演示展示从一条命令到可继续创作项目的最小闭环。全部人物、地点和设定均为原创示例。

## 1. 初始化项目

```bash
python3 scripts/manage_novel_project.py init \
  --mode professional \
  --title "雾港回声" \
  --genre "都市重生" \
  --golden-finger "旧物记忆回溯" \
  --core-tropes "破局逆袭" \
  --protagonist "闻人澈" \
  --heroine "阮栖月" \
  --antagonist "柏砚川" \
  --chapters 3
```

## 2. 得到可编辑的项目结构

```text
web-novels/
  <timestamp>-雾港回声/
    00-大纲.md
    01-人物档案.md
    02-名场面时间轴.md
    03-写作计划.json
    04-章节详细规划.md
    chapters/
```

`03-写作计划.json` 保存章节状态、伏笔、命名台账和质量阈值；正文与设定资料由作者或协作助手在项目目录中持续补全。

## 3. 校验创作基线

```bash
python3 scripts/manage_novel_project.py validate ./web-novels/<项目目录>
```

校验会检查项目结构、章节字数、占位内容、命名重复和章节状态，并写入 `QC校验报告.md`。它通过的是自动基线，发布前仍应人工复核原创性、剧情连续性、事实资料与平台最新规范。

下一步可以查看 [原创示例项目](../examples/urban-rebirth-starter/README.md)，或在连载时使用 [连续创作模板](../references/guides/Serial-Continuity-Template.md)。
