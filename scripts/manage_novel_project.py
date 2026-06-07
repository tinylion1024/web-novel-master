#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网文项目管理工具。

提供最小可执行工具链：
1. init: 初始化项目目录与基础文件
2. resume: 扫描可续写项目
3. set-status: 更新项目或章节状态
4. validate: 批量校验章节并生成 QC 报告
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
WEB_NOVELS_DIR = ROOT_DIR / "web-novels"
PLAN_FILE_NAME = "03-写作计划.json"
RUBRIC_PATH = ROOT_DIR / "references" / "Check" / "Quality-Rubric.json"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_chapter_wordcount import check_chapter, extract_content_from_chapter  # noqa: E402


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "-", name).strip().strip(".")


def chapter_filename(chapter_number: int) -> str:
    return f"chapters/第{chapter_number:02d}章.md"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_rubric() -> dict[str, Any]:
    return load_json(RUBRIC_PATH)


def project_dir_from_plan(plan: dict[str, Any]) -> Path:
    project_path = plan.get("projectPath", "").removeprefix("./")
    if project_path:
        return ROOT_DIR / project_path
    raise ValueError("写作计划缺少 projectPath")


def find_plan_file(project_dir: Path) -> Path:
    plan_path = project_dir / PLAN_FILE_NAME
    if not plan_path.exists():
        raise FileNotFoundError(f"未找到 {PLAN_FILE_NAME}: {project_dir}")
    return plan_path


def load_plan(project_dir: Path) -> tuple[Path, dict[str, Any]]:
    plan_path = find_plan_file(project_dir)
    return plan_path, load_json(plan_path)


def build_plan(args: argparse.Namespace, project_dir: Path) -> dict[str, Any]:
    created_at = now_iso()
    chapters = []
    for number in range(1, args.chapters + 1):
        title = args.chapter_titles[number - 1] if args.chapter_titles and number <= len(args.chapter_titles) else f"第{number:02d}章"
        chapters.append(
            {
                "chapterNumber": number,
                "title": title,
                "filePath": chapter_filename(number),
                "status": "pending",
                "wordCount": None,
                "wordCountPass": None,
                "famousScene": "",
                "famousSceneDesc": "",
                "emotionalArc": "",
                "foreshadow": {"seeds": [], "resolves": []},
                "retryCount": 0,
                "validation": None,
            }
        )

    optional_files = ["02-名场面时间轴.md", "04-章节详细规划.md"]
    if args.mode == "industrial":
        optional_files.append("05-伏笔系统.md")

    return {
        "version": 3,
        "mode": args.mode,
        "novelName": args.title,
        "projectPath": f"./web-novels/{project_dir.name}",
        "totalChapters": args.chapters,
        "minWordsPerChapter": args.min_words,
        "maxWordsPerChapter": args.max_words,
        "createdAt": created_at,
        "updatedAt": created_at,
        "status": "planning",
        "writingMode": args.writing_mode,
        "requiredFiles": [
            "00-大纲.md",
            "01-人物档案.md",
            PLAN_FILE_NAME,
            "chapters/"
        ],
        "optionalFiles": optional_files,
        "coreSetting": {
            "genre": args.genre,
            "goldenFinger": args.golden_finger,
            "coreTropes": args.core_tropes,
        },
        "characters": {
            "protagonist": args.protagonist,
            "heroine": args.heroine,
            "antagonist": args.antagonist,
        },
        "chapters": chapters,
    }


def outline_template(plan: dict[str, Any]) -> str:
    title = plan["novelName"]
    core = plan["coreSetting"]
    total = plan["totalChapters"]
    first_title = plan["chapters"][0]["title"] if plan["chapters"] else "第01章"
    return f"""# {title}

## 基本信息
- 类型：{core["genre"]}
- 金手指：{core["goldenFinger"]}
- 核心爽点：{core["coreTropes"]}
- 章节数：{total} 章

## 核心设定

### 金手指设计
- 类型：{core["goldenFinger"]}
- 激活条件：待补充
- 使用限制：待补充
- 升级方式：待补充

### 势力分布
- 主角阵营：待补充
- 主要反派势力：待补充

## 章节规划

### {first_title}
- 核心事件：待补充
- 爽点设计：待补充
- 承接：无（首章）
- 悬念钩子：待补充
- 情绪弧线：压抑 -> 释放
- 伏笔：待补充
"""


def character_template(plan: dict[str, Any]) -> str:
    characters = plan["characters"]
    return f"""# {plan["novelName"]} 人物档案

## 主角
- 姓名：{characters["protagonist"]}
- 身份：待补充
- 性格：待补充
- 金手指：{plan["coreSetting"]["goldenFinger"]}

## 女主
- 姓名：{characters["heroine"] or "待补充"}
- 关系：待补充

## 反派
- 姓名/代号：{characters["antagonist"] or "待补充"}
- 压迫感来源：待补充
"""


def simple_markdown(title: str, body: str) -> str:
    return f"# {title}\n\n{body.rstrip()}\n"


def init_project(args: argparse.Namespace) -> int:
    WEB_NOVELS_DIR.mkdir(parents=True, exist_ok=True)
    project_name = f"{timestamp_slug()}-{safe_name(args.title)}"
    project_dir = WEB_NOVELS_DIR / project_name

    if project_dir.exists():
        raise FileExistsError(f"项目目录已存在: {project_dir}")

    plan = build_plan(args, project_dir)

    (project_dir / "chapters").mkdir(parents=True, exist_ok=True)
    save_json(project_dir / PLAN_FILE_NAME, plan)
    (project_dir / "00-大纲.md").write_text(outline_template(plan), encoding="utf-8")
    (project_dir / "01-人物档案.md").write_text(character_template(plan), encoding="utf-8")
    (project_dir / "02-名场面时间轴.md").write_text(
        simple_markdown("名场面时间轴", "| 章节 | 类型 | 描述 |\n|------|------|------|\n| 第1章 | 待补充 | 待补充 |"),
        encoding="utf-8",
    )
    (project_dir / "04-章节详细规划.md").write_text(
        simple_markdown("章节详细规划", "## 第01章\n\n- 核心事件：待补充\n- 爽点设计：待补充\n- 悬念钩子：待补充"),
        encoding="utf-8",
    )
    if args.mode == "industrial":
        (project_dir / "05-伏笔系统.md").write_text(
            simple_markdown("伏笔系统", "| 伏笔ID | 章节 | 描述 | 回收章节 | 状态 |\n|--------|------|------|----------|------|"),
            encoding="utf-8",
        )

    print(f"项目已初始化: {project_dir}")
    print(f"写作计划: {project_dir / PLAN_FILE_NAME}")
    return 0


def list_resumable_projects(_args: argparse.Namespace) -> int:
    if not WEB_NOVELS_DIR.exists():
        print("未找到 web-novels 目录")
        return 0

    rows = []
    for plan_path in WEB_NOVELS_DIR.glob(f"*/{PLAN_FILE_NAME}"):
        plan = load_json(plan_path)
        status = plan.get("status", "unknown")
        if status == "completed":
            continue
        chapters = plan.get("chapters", [])
        completed = sum(1 for item in chapters if item.get("status") == "completed")
        rows.append(
            {
                "project": plan.get("novelName", plan_path.parent.name),
                "path": str(plan_path.parent.relative_to(ROOT_DIR)),
                "status": status,
                "progress": f"{completed}/{len(chapters)}",
                "updatedAt": plan.get("updatedAt", ""),
            }
        )

    if not rows:
        print("没有可续写项目")
        return 0

    rows.sort(key=lambda row: row["updatedAt"], reverse=True)
    print("可续写项目：")
    for row in rows:
        print(f"- {row['project']} | {row['status']} | {row['progress']} | {row['path']}")
    return 0


def update_plan_status(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    plan_path, plan = load_plan(project_dir)
    changed = False

    if args.project_status:
        plan["status"] = args.project_status
        changed = True

    if args.chapter is not None:
        matched = None
        for chapter in plan.get("chapters", []):
            if chapter.get("chapterNumber") == args.chapter:
                matched = chapter
                break
        if matched is None:
            raise ValueError(f"未找到章节: {args.chapter}")

        if args.chapter_status:
            matched["status"] = args.chapter_status
            changed = True
        if args.word_count is not None:
            matched["wordCount"] = args.word_count
            matched["wordCountPass"] = args.word_count >= plan.get("minWordsPerChapter", 2000)
            changed = True
        if args.note:
            matched["note"] = args.note
            changed = True

    if not changed:
        print("没有变更要写入")
        return 0

    plan["updatedAt"] = now_iso()
    save_json(plan_path, plan)
    print(f"已更新: {plan_path}")
    return 0


def evaluate_opening_hook(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    opening = text[: rule["openingWindow"]]
    found_keyword = next((keyword for keyword in rule["keywords"] if keyword in opening), None)
    found_punctuation = "？" in opening or "！" in opening
    passed = bool(found_keyword or found_punctuation)
    if found_keyword:
        reason = f"命中关键词：{found_keyword}"
    elif found_punctuation:
        reason = "命中强情绪标点"
    else:
        reason = "前段缺少明显冲突或悬念"
    return passed, reason


def evaluate_excitement_density(text: str, word_count: int, rule: dict[str, Any]) -> tuple[bool, str]:
    hits = sum(text.count(keyword) for keyword in rule["keywords"])
    minimum_hits = max(1, math.ceil(word_count / 2000 * rule["minimumHitsPer2000Chars"]))
    passed = hits >= minimum_hits
    return passed, f"爽点命中 {hits} 次，要求至少 {minimum_hits} 次"


def evaluate_emotional_rhythm(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    midpoint = max(1, len(text) // 2)
    first_half = text[:midpoint]
    second_half = text[midpoint:]
    negative = next((item for item in rule["negativeKeywords"] if item in first_half), None)
    positive = next((item for item in rule["positiveKeywords"] if item in second_half), None)
    passed = bool(negative and positive)
    return passed, f"前半压迫：{negative or '未命中'}；后半释放：{positive or '未命中'}"


def evaluate_quote_line(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    minimum_length = rule["minimumQuotedLineLength"]
    matches = re.findall(r"[“\"]([^”\"]+)[”\"]", text)
    passed = any(len(item) >= minimum_length for item in matches)
    longest = max((len(item) for item in matches), default=0)
    return passed, f"最长引号句长度 {longest}"


def evaluate_ending_hook(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    ending = text[-rule["endingWindow"]:]
    found_keyword = next((keyword for keyword in rule["keywords"] if keyword in ending), None)
    passed = bool(found_keyword)
    return passed, f"结尾命中：{found_keyword or '无'}"


def evaluate_chapter(chapter_path: Path, min_words: int, rubric: dict[str, Any]) -> dict[str, Any]:
    chapter_check = check_chapter(str(chapter_path), min_words)
    if not chapter_check["exists"]:
        return {
            "path": str(chapter_path),
            "exists": False,
            "score": 0,
            "passed": False,
            "checks": {
                "word_count": {
                    "passed": False,
                    "score": 0,
                    "reason": chapter_check["message"],
                }
            },
            "wordCount": 0,
        }

    text = extract_content_from_chapter(chapter_path)
    word_count = chapter_check["word_count"]
    checks: dict[str, Any] = {}
    total_score = 0

    for rule in rubric["checks"]:
        check_id = rule["id"]
        passed = False
        reason = ""
        if check_id == "word_count":
            passed = word_count >= rule["minimumWords"]
            reason = f"字数 {word_count} / 最低 {rule['minimumWords']}"
        elif check_id == "opening_hook":
            passed, reason = evaluate_opening_hook(text, rule)
        elif check_id == "excitement_density":
            passed, reason = evaluate_excitement_density(text, word_count, rule)
        elif check_id == "emotional_rhythm":
            passed, reason = evaluate_emotional_rhythm(text, rule)
        elif check_id == "quote_line":
            passed, reason = evaluate_quote_line(text, rule)
        elif check_id == "ending_hook":
            passed, reason = evaluate_ending_hook(text, rule)

        score = rule["weight"] if passed else 0
        total_score += score
        checks[check_id] = {
            "passed": passed,
            "score": score,
            "weight": rule["weight"],
            "reason": reason,
            "description": rule["description"],
        }

    passed = total_score >= rubric["minimumScore"] and chapter_check["status"] == "pass"
    return {
        "path": str(chapter_path),
        "exists": True,
        "score": total_score,
        "passed": passed,
        "checks": checks,
        "wordCount": word_count,
    }


def write_qc_report(project_dir: Path, plan: dict[str, Any], results: list[dict[str, Any]], rubric: dict[str, Any]) -> Path:
    lines = [
        f"# {plan['novelName']} QC 校验报告",
        "",
        "## 项目概览",
        f"- 项目路径：`{project_dir.relative_to(ROOT_DIR)}`",
        f"- 写作模式：`{plan.get('mode', 'unknown')}`",
        f"- 最低通过分：`{rubric['minimumScore']}`",
        f"- 校验时间：`{now_iso()}`",
        "",
        "## 章节结果",
        "",
        "| 章节 | 状态 | 字数 | 评分 | 未通过项 |",
        "|------|------|------|------|----------|",
    ]

    for chapter, result in zip(plan.get("chapters", []), results):
        failed_checks = [
            check["description"]
            for check in result["checks"].values()
            if not check["passed"]
        ]
        lines.append(
            f"| 第{chapter['chapterNumber']:02d}章 | "
            f"{'通过' if result['passed'] else '未通过'} | "
            f"{result['wordCount']} | "
            f"{result['score']} | "
            f"{'；'.join(failed_checks) if failed_checks else '无'} |"
        )

    lines.extend(["", "## 详细原因", ""])
    for chapter, result in zip(plan.get("chapters", []), results):
        lines.append(f"### 第{chapter['chapterNumber']:02d}章：{chapter['title']}")
        for check_id, check in result["checks"].items():
            marker = "PASS" if check["passed"] else "FAIL"
            lines.append(f"- `{check_id}` [{marker}] {check['reason']}")
        lines.append("")

    report_path = project_dir / "QC校验报告.md"
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return report_path


def validate_project(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    plan_path, plan = load_plan(project_dir)
    rubric = load_rubric()
    results = []

    plan["status"] = "validating"
    plan["updatedAt"] = now_iso()

    for chapter in plan.get("chapters", []):
        chapter_path = project_dir / chapter["filePath"]
        result = evaluate_chapter(chapter_path, plan.get("minWordsPerChapter", 2000), rubric)
        chapter["wordCount"] = result["wordCount"]
        chapter["wordCountPass"] = result["checks"]["word_count"]["passed"]
        chapter["validation"] = {
            "score": result["score"],
            "passed": result["passed"],
            "checks": result["checks"],
        }
        chapter["status"] = "completed" if result["passed"] else "failed"
        if not result["passed"]:
            chapter["retryCount"] = int(chapter.get("retryCount", 0)) + 1
        results.append(result)

    plan["status"] = "completed" if all(item["passed"] for item in results) else "failed"
    plan["updatedAt"] = now_iso()
    save_json(plan_path, plan)

    report_path = write_qc_report(project_dir, plan, results, rubric)
    passed_count = sum(1 for item in results if item["passed"])
    print(f"校验完成: {passed_count}/{len(results)} 章通过")
    print(f"计划状态: {plan['status']}")
    print(f"QC 报告: {report_path}")
    return 0 if plan["status"] == "completed" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Web Novel Master 项目管理工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化一个新项目")
    init_parser.add_argument("--mode", choices=["fast", "professional", "industrial", "instant"], default="professional")
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--genre", required=True)
    init_parser.add_argument("--golden-finger", required=True, dest="golden_finger")
    init_parser.add_argument("--core-tropes", required=True, dest="core_tropes")
    init_parser.add_argument("--chapters", type=int, default=1)
    init_parser.add_argument("--min-words", type=int, default=2000, dest="min_words")
    init_parser.add_argument("--max-words", type=int, default=3000, dest="max_words")
    init_parser.add_argument("--writing-mode", choices=["serial", "subagent-parallel", "agent-teams"], default="serial", dest="writing_mode")
    init_parser.add_argument("--protagonist", default="待补充")
    init_parser.add_argument("--heroine", default="")
    init_parser.add_argument("--antagonist", default="")
    init_parser.add_argument("--chapter-titles", nargs="*", default=[])
    init_parser.set_defaults(func=init_project)

    resume_parser = subparsers.add_parser("resume", help="扫描可续写项目")
    resume_parser.set_defaults(func=list_resumable_projects)

    status_parser = subparsers.add_parser("set-status", help="更新项目或章节状态")
    status_parser.add_argument("project_dir")
    status_parser.add_argument("--project-status", choices=["planning", "in_progress", "validating", "completed", "failed"])
    status_parser.add_argument("--chapter", type=int)
    status_parser.add_argument("--chapter-status", choices=["pending", "in_progress", "completed", "failed"])
    status_parser.add_argument("--word-count", type=int, dest="word_count")
    status_parser.add_argument("--note")
    status_parser.set_defaults(func=update_plan_status)

    validate_parser = subparsers.add_parser("validate", help="批量校验项目章节并生成 QC 报告")
    validate_parser.add_argument("project_dir")
    validate_parser.set_defaults(func=validate_project)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
