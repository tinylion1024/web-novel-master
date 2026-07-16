#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""网文项目管理工具。"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
WEB_NOVELS_DIR = ROOT_DIR / "web-novels"
PLAN_FILE_NAME = "03-写作计划.json"
RUBRIC_PATH = ROOT_DIR / "references" / "Check" / "Quality-Rubric.json"
LATEST_PLAN_VERSION = 4
PLAN_LOCK_TIMEOUT_SECONDS = 10

PROJECT_STATUSES = {"planning", "in_progress", "validating", "completed", "failed"}
CHAPTER_STATUSES = {"pending", "in_progress", "completed", "failed"}
PROJECT_TRANSITIONS = {
    "planning": {"planning", "in_progress", "validating", "failed"},
    "in_progress": {"in_progress", "validating", "failed"},
    "validating": {"validating", "completed", "failed"},
    "failed": {"failed", "in_progress", "validating"},
    "completed": {"completed"},
}
CHAPTER_TRANSITIONS = {
    "pending": {"pending", "in_progress", "failed"},
    "in_progress": {"in_progress", "completed", "failed"},
    "failed": {"failed", "in_progress"},
    "completed": {"completed"},
}
DEFAULT_AVOID_SURNAMES = ["林", "顾", "沈", "苏", "叶", "秦", "萧", "楚", "陆", "傅", "江", "韩"]
LEDGER_FIELDS = ("usedPersonNames", "usedPlaceNames", "usedOrganizations", "usedArtifacts")

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


def atomic_write_text(path: Path, content: str) -> None:
    """Write a complete replacement before publishing it with os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON 根节点必须是对象: {path}")
    return payload


def save_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


@contextmanager
def plan_lock(plan_path: Path, timeout_seconds: float = PLAN_LOCK_TIMEOUT_SECONDS) -> Iterator[None]:
    """Serialize read-modify-write operations performed by this CLI."""
    lock_path = plan_path.with_suffix(plan_path.suffix + ".lock")
    deadline = time.monotonic() + timeout_seconds
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"pid={os.getpid()} createdAt={now_iso()}\n".encode("utf-8"))
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"写作计划正被其他任务更新: {lock_path}")
            time.sleep(0.1)
    try:
        yield
    finally:
        os.close(descriptor)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def load_rubric() -> dict[str, Any]:
    rubric = load_json(RUBRIC_PATH)
    if rubric.get("version") != 2 or not isinstance(rubric.get("checks"), list):
        raise ValueError("质量评分规则必须使用 version 2 格式")
    return rubric


def default_naming_ledger() -> dict[str, Any]:
    return {
        "usedPersonNames": [],
        "usedPlaceNames": [],
        "usedOrganizations": [],
        "usedArtifacts": [],
        "defaultAvoidSurnames": list(DEFAULT_AVOID_SURNAMES),
    }


def normalize_naming_ledger(value: Any) -> dict[str, Any]:
    ledger = dict(value) if isinstance(value, dict) else {}
    legacy_surnames = ledger.pop("blockedHighFrequency", None)
    for field in LEDGER_FIELDS:
        ledger.setdefault(field, [])
    ledger.setdefault(
        "defaultAvoidSurnames",
        legacy_surnames if isinstance(legacy_surnames, list) else list(DEFAULT_AVOID_SURNAMES),
    )
    return ledger


def migrate_plan(plan: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Normalize v1-v3 project plans into the v4 contract without losing data."""
    migrated = dict(plan)
    source_version = migrated.get("version", 1)
    if not isinstance(source_version, int) or source_version < 1 or source_version > LATEST_PLAN_VERSION:
        raise ValueError(f"不支持的写作计划版本: {source_version}")

    changed = source_version != LATEST_PLAN_VERSION
    migrated.setdefault("mode", "professional")
    migrated.setdefault("writingMode", "serial")
    migrated.setdefault("status", "planning")
    if migrated["status"] == "initializing":
        migrated["status"] = "planning"
        changed = True
    migrated.setdefault("requiredFiles", ["00-大纲.md", "01-人物档案.md", PLAN_FILE_NAME, "chapters/"])
    migrated.setdefault("optionalFiles", ["02-名场面时间轴.md", "04-章节详细规划.md"])
    migrated.setdefault("minWordsPerChapter", 2000)
    migrated.setdefault("maxWordsPerChapter", 3000)
    migrated.setdefault("createdAt", now_iso())
    migrated.setdefault("updatedAt", migrated["createdAt"])

    core_setting = dict(migrated.get("coreSetting") or {})
    core_setting.setdefault("genre", "待补充")
    core_setting.setdefault("goldenFinger", "待补充")
    core_setting.setdefault("coreTropes", "待补充")
    migrated["coreSetting"] = core_setting

    migrated["namingLedger"] = normalize_naming_ledger(migrated.get("namingLedger"))
    chapters = migrated.get("chapters")
    if not isinstance(chapters, list):
        chapters = []
    normalized_chapters = []
    for index, value in enumerate(chapters, start=1):
        chapter = dict(value) if isinstance(value, dict) else {}
        number = chapter.get("chapterNumber", index)
        chapter.setdefault("chapterNumber", number)
        chapter.setdefault("title", f"第{number:02d}章" if isinstance(number, int) else f"第{index:02d}章")
        chapter.setdefault("filePath", chapter_filename(number if isinstance(number, int) else index))
        chapter.setdefault("status", "pending")
        chapter.setdefault("wordCount", None)
        chapter.setdefault("wordCountPass", None)
        chapter.setdefault("famousScene", "")
        chapter.setdefault("famousSceneDesc", "")
        chapter.setdefault("emotionalArc", "")
        chapter.setdefault("foreshadow", {"seeds": [], "resolves": []})
        chapter.setdefault("retryCount", 0)
        chapter.setdefault("validation", None)
        normalized_chapters.append(chapter)
    migrated["chapters"] = normalized_chapters
    migrated.setdefault("totalChapters", len(normalized_chapters))
    migrated["version"] = LATEST_PLAN_VERSION
    return migrated, changed


def validate_naming_ledger(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    ledger = plan.get("namingLedger", {})
    errors: list[str] = []
    warnings: list[str] = []
    names: list[str] = []
    for field in LEDGER_FIELDS:
        values = ledger.get(field)
        if not isinstance(values, list) or not all(isinstance(item, str) and item.strip() for item in values):
            errors.append(f"namingLedger.{field} 必须是非空字符串数组")
            continue
        names.extend(item.strip() for item in values)

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        errors.append(f"命名台账存在重复名称: {'、'.join(duplicates)}")

    avoid_surnames = ledger.get("defaultAvoidSurnames")
    if not isinstance(avoid_surnames, list) or not all(isinstance(item, str) for item in avoid_surnames):
        errors.append("namingLedger.defaultAvoidSurnames 必须是字符串数组")
        avoid_surnames = []
    high_frequency = [name for name in ledger.get("usedPersonNames", []) if name and name[0] in avoid_surnames]
    if high_frequency:
        warnings.append(f"使用了默认应避免的高频姓氏: {'、'.join(high_frequency)}")

    people = ledger.get("usedPersonNames", [])
    leading_characters = [name[0] for name in people if name]
    if len(leading_characters) >= 3 and len(set(leading_characters)) < len(leading_characters):
        warnings.append("多个核心角色首字重复，建议检查姓名音形区分度")

    generic_places = {"县城", "京城", "魔都", "小镇", "大城市", "边城", "省城"}
    generic_values = [name for name in ledger.get("usedPlaceNames", []) if name in generic_places]
    if generic_values:
        warnings.append(f"地名仍是泛称，建议改用正式名称: {'、'.join(generic_values)}")
    return errors, warnings


def validate_plan_data(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if plan.get("version") != LATEST_PLAN_VERSION:
        errors.append(f"version 必须为 {LATEST_PLAN_VERSION}")
    total = plan.get("totalChapters")
    if not isinstance(total, int) or isinstance(total, bool) or total < 1:
        errors.append("totalChapters 必须是大于 0 的整数")
        total = 0
    min_words = plan.get("minWordsPerChapter")
    max_words = plan.get("maxWordsPerChapter")
    if not isinstance(min_words, int) or isinstance(min_words, bool) or min_words < 1:
        errors.append("minWordsPerChapter 必须是正整数")
    if not isinstance(max_words, int) or isinstance(max_words, bool) or max_words < 1:
        errors.append("maxWordsPerChapter 必须是正整数")
    elif isinstance(min_words, int) and max_words < min_words:
        errors.append("maxWordsPerChapter 不能小于 minWordsPerChapter")

    if plan.get("status") not in PROJECT_STATUSES:
        errors.append("status 不在允许的项目状态集合中")
    if plan.get("mode") not in {"fast", "professional", "industrial", "instant"}:
        errors.append("mode 不在允许的创作模式集合中")
    if plan.get("writingMode") not in {"serial", "subagent-parallel", "agent-teams"}:
        errors.append("writingMode 不在允许的写作模式集合中")
    if not isinstance(plan.get("projectPath"), str) or not plan["projectPath"].startswith("./web-novels/"):
        errors.append("projectPath 必须位于 ./web-novels/ 下")

    chapters = plan.get("chapters")
    if not isinstance(chapters, list):
        errors.append("chapters 必须是数组")
        chapters = []
    if len(chapters) != total:
        errors.append("chapters 数量必须与 totalChapters 一致")
    numbers: list[int] = []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            errors.append("chapters 中每项必须是对象")
            continue
        number = chapter.get("chapterNumber")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            errors.append("chapterNumber 必须是正整数")
            continue
        numbers.append(number)
        if chapter.get("status") not in CHAPTER_STATUSES:
            errors.append(f"第{number}章状态非法")
        file_path = chapter.get("filePath")
        if not isinstance(file_path, str) or Path(file_path).is_absolute() or ".." in Path(file_path).parts:
            errors.append(f"第{number}章 filePath 必须是安全相对路径")
        elif file_path != chapter_filename(number):
            errors.append(f"第{number}章 filePath 必须为 {chapter_filename(number)}")
    if len(numbers) != len(set(numbers)):
        errors.append("chapterNumber 不能重复")
    if numbers and sorted(numbers) != list(range(1, len(numbers) + 1)):
        errors.append("chapterNumber 必须从 1 连续编号")

    naming_errors, naming_warnings = validate_naming_ledger(plan)
    errors.extend(naming_errors)
    return errors, naming_warnings


def find_plan_file(project_dir: Path) -> Path:
    plan_path = project_dir / PLAN_FILE_NAME
    if not plan_path.exists():
        raise FileNotFoundError(f"未找到 {PLAN_FILE_NAME}: {project_dir}")
    return plan_path


def load_plan(project_dir: Path) -> tuple[Path, dict[str, Any]]:
    plan_path = find_plan_file(project_dir)
    plan, _ = migrate_plan(load_json(plan_path))
    if not plan.get("projectPath"):
        plan["projectPath"] = f"./web-novels/{project_dir.name}"
    errors, _ = validate_plan_data(plan)
    if errors:
        raise ValueError("写作计划格式无效: " + "；".join(errors))
    return plan_path, plan


def validate_init_args(args: argparse.Namespace) -> None:
    if not safe_name(args.title):
        raise ValueError("小说标题不能为空或仅包含非法文件名字符")
    if args.chapters < 1:
        raise ValueError("章节数必须大于 0")
    if args.min_words < 1:
        raise ValueError("最小字数必须大于 0")
    if args.max_words < args.min_words:
        raise ValueError("最大字数不能小于最小字数")


def build_plan(args: argparse.Namespace, project_dir: Path) -> dict[str, Any]:
    validate_init_args(args)
    created_at = now_iso()
    used_person_names = [name for name in [args.protagonist, args.heroine, args.antagonist] if name and name != "待补充"]
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
        "version": LATEST_PLAN_VERSION,
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
        "requiredFiles": ["00-大纲.md", "01-人物档案.md", PLAN_FILE_NAME, "chapters/"],
        "optionalFiles": optional_files,
        "coreSetting": {"genre": args.genre, "goldenFinger": args.golden_finger, "coreTropes": args.core_tropes},
        "namingLedger": {**default_naming_ledger(), "usedPersonNames": used_person_names},
        "characters": {"protagonist": args.protagonist, "heroine": args.heroine, "antagonist": args.antagonist},
        "chapters": chapters,
    }


def outline_template(plan: dict[str, Any]) -> str:
    core = plan["coreSetting"]
    first_title = plan["chapters"][0]["title"]
    return f"""# {plan["novelName"]}

## 基本信息
- 类型：{core["genre"]}
- 金手指：{core["goldenFinger"]}
- 核心爽点：{core["coreTropes"]}
- 核心舞台：待补充正式地名
- 章节数：{plan["totalChapters"]} 章

## 核心设定

### 金手指设计
- 类型：{core["goldenFinger"]}
- 激活条件：待补充
- 使用限制：待补充
- 升级方式：待补充

### 势力分布
- 主角阵营：待补充
- 主要反派势力：待补充

### 命名约束
- 使用 `03-写作计划.json` 的 `namingLedger` 查重
- 用户未指定时，避免优先使用高频默认姓氏和泛化地点

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
- 命名来源：待补充
- 身份：待补充
- 性格：待补充
- 金手指：{plan["coreSetting"]["goldenFinger"]}

## 女主
- 姓名：{characters["heroine"] or "待补充"}
- 命名来源：待补充
- 关系：待补充

## 反派
- 姓名/代号：{characters["antagonist"] or "待补充"}
- 命名来源：待补充
- 压迫感来源：待补充
"""


def simple_markdown(title: str, body: str) -> str:
    return f"# {title}\n\n{body.rstrip()}\n"


def init_project(args: argparse.Namespace) -> int:
    validate_init_args(args)
    WEB_NOVELS_DIR.mkdir(parents=True, exist_ok=True)
    project_dir = WEB_NOVELS_DIR / f"{timestamp_slug()}-{safe_name(args.title)}"
    if project_dir.exists():
        raise FileExistsError(f"项目目录已存在: {project_dir}")
    plan = build_plan(args, project_dir)
    (project_dir / "chapters").mkdir(parents=True, exist_ok=True)
    save_json(project_dir / PLAN_FILE_NAME, plan)
    atomic_write_text(project_dir / "00-大纲.md", outline_template(plan))
    atomic_write_text(project_dir / "01-人物档案.md", character_template(plan))
    atomic_write_text(project_dir / "02-名场面时间轴.md", simple_markdown("名场面时间轴", "| 章节 | 类型 | 描述 |\n|------|------|------|\n| 第1章 | 待补充 | 待补充 |"))
    atomic_write_text(project_dir / "04-章节详细规划.md", simple_markdown("章节详细规划", "## 第01章\n\n- 核心事件：待补充\n- 爽点设计：待补充\n- 悬念钩子：待补充"))
    if args.mode == "industrial":
        atomic_write_text(project_dir / "05-伏笔系统.md", simple_markdown("伏笔系统", "| 伏笔ID | 章节 | 描述 | 回收章节 | 状态 |\n|--------|------|------|----------|------|"))
    print(f"项目已初始化: {project_dir}")
    print(f"写作计划: {project_dir / PLAN_FILE_NAME}")
    return 0


def list_resumable_projects(_args: argparse.Namespace) -> int:
    if not WEB_NOVELS_DIR.exists():
        print("未找到 web-novels 目录")
        return 0
    rows = []
    for plan_path in WEB_NOVELS_DIR.glob(f"*/{PLAN_FILE_NAME}"):
        try:
            _, plan = load_plan(plan_path.parent)
        except (ValueError, json.JSONDecodeError) as error:
            print(f"跳过损坏项目 {plan_path.parent.name}: {error}", file=sys.stderr)
            continue
        if plan["status"] == "completed":
            continue
        completed = sum(1 for item in plan["chapters"] if item["status"] == "completed")
        rows.append({"project": plan.get("novelName", plan_path.parent.name), "path": str(plan_path.parent.relative_to(ROOT_DIR)), "status": plan["status"], "progress": f"{completed}/{len(plan['chapters'])}", "updatedAt": plan.get("updatedAt", "")})
    if not rows:
        print("没有可续写项目")
        return 0
    for row in sorted(rows, key=lambda item: item["updatedAt"], reverse=True):
        print(f"- {row['project']} | {row['status']} | {row['progress']} | {row['path']}")
    return 0


def ensure_transition(current: str, target: str, transitions: dict[str, set[str]], label: str) -> None:
    if target not in transitions.get(current, set()):
        raise ValueError(f"{label}状态不能从 {current} 变为 {target}")


def update_plan_status(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    plan_path = find_plan_file(project_dir)
    with plan_lock(plan_path):
        _, plan = load_plan(project_dir)
        changed = False
        if args.project_status:
            ensure_transition(plan["status"], args.project_status, PROJECT_TRANSITIONS, "项目")
            plan["status"] = args.project_status
            changed = True
        if args.chapter is not None:
            matched = next((chapter for chapter in plan["chapters"] if chapter["chapterNumber"] == args.chapter), None)
            if matched is None:
                raise ValueError(f"未找到章节: {args.chapter}")
            if args.chapter_status:
                ensure_transition(matched["status"], args.chapter_status, CHAPTER_TRANSITIONS, "章节")
                matched["status"] = args.chapter_status
                changed = True
            if args.word_count is not None:
                if args.word_count < 0:
                    raise ValueError("章节字数不能为负数")
                matched["wordCount"] = args.word_count
                matched["wordCountPass"] = plan["minWordsPerChapter"] <= args.word_count <= plan["maxWordsPerChapter"]
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


def evaluate_word_count(word_count: int, min_words: int, max_words: int) -> tuple[bool, str]:
    passed = min_words <= word_count <= max_words
    return passed, f"字数 {word_count} / 允许范围 {min_words}-{max_words}"


def evaluate_content_integrity(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    unique_count = len(set(chinese_chars))
    repeated_runs = [len(match.group(0)) for match in re.finditer(r"(.)\1+", text)]
    longest_run = max(repeated_runs, default=1)
    minimum_unique = rule["minimumUniqueChineseCharacters"]
    maximum_run = rule["maximumRepeatedCharacterRun"]
    passed = unique_count >= minimum_unique and longest_run <= maximum_run
    return passed, f"不同汉字 {unique_count}/{minimum_unique}；最长重复字符 {longest_run}/{maximum_run}"


def evaluate_opening_hook(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    opening = text[: rule["openingWindow"]]
    hits = [keyword for keyword in rule["keywords"] if keyword in opening]
    passed = len(hits) >= rule["minimumDistinctKeywords"]
    return passed, f"开篇命中：{'、'.join(hits) if hits else '无'}"


def evaluate_excitement_density(text: str, word_count: int, rule: dict[str, Any]) -> tuple[bool, str]:
    hit_count = sum(text.count(keyword) for keyword in rule["keywords"])
    distinct_hits = [keyword for keyword in rule["keywords"] if keyword in text]
    minimum_hits = max(1, math.ceil(word_count / 2000 * rule["minimumHitsPer2000Chars"]))
    passed = hit_count >= minimum_hits and len(distinct_hits) >= rule["minimumDistinctKeywords"]
    return passed, f"爽点命中 {hit_count}/{minimum_hits} 次；不同关键词 {len(distinct_hits)}/{rule['minimumDistinctKeywords']}"


def evaluate_emotional_rhythm(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    midpoint = max(1, len(text) // 2)
    negative = next((item for item in rule["negativeKeywords"] if item in text[:midpoint]), None)
    positive = next((item for item in rule["positiveKeywords"] if item in text[midpoint:]), None)
    return bool(negative and positive), f"前半压迫：{negative or '未命中'}；后半释放：{positive or '未命中'}"


def evaluate_quote_line(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    matches = re.findall(r"[“\"]([^”\"]+)[”\"]", text)
    longest = max((len(item) for item in matches), default=0)
    return longest >= rule["minimumQuotedLineLength"], f"最长引号句长度 {longest}"


def evaluate_ending_hook(text: str, rule: dict[str, Any]) -> tuple[bool, str]:
    ending = text[-rule["endingWindow"]:]
    hits = [keyword for keyword in rule["keywords"] if keyword in ending]
    return bool(hits), f"结尾命中：{'、'.join(hits) if hits else '无'}"


def evaluate_chapter(chapter_path: Path, min_words: int, max_words: int, rubric: dict[str, Any]) -> dict[str, Any]:
    chapter_check = check_chapter(str(chapter_path), min_words)
    if not chapter_check["exists"]:
        return {"path": str(chapter_path), "exists": False, "score": 0, "passed": False, "manualReviewRequired": True, "checks": {"word_count": {"passed": False, "score": 0, "weight": 0, "required": True, "reason": chapter_check["message"], "description": "章节文件存在且字数达标"}}, "wordCount": 0}
    text = extract_content_from_chapter(chapter_path)
    word_count = chapter_check["word_count"]
    handlers = {
        "word_count": lambda rule: evaluate_word_count(word_count, min_words, max_words),
        "content_integrity": lambda rule: evaluate_content_integrity(text, rule),
        "opening_hook": lambda rule: evaluate_opening_hook(text, rule),
        "excitement_density": lambda rule: evaluate_excitement_density(text, word_count, rule),
        "emotional_rhythm": lambda rule: evaluate_emotional_rhythm(text, rule),
        "quote_line": lambda rule: evaluate_quote_line(text, rule),
        "ending_hook": lambda rule: evaluate_ending_hook(text, rule),
    }
    checks: dict[str, Any] = {}
    total_score = 0
    required_passed = True
    for rule in rubric["checks"]:
        check_id = rule["id"]
        if check_id not in handlers:
            raise ValueError(f"未知质量规则: {check_id}")
        passed, reason = handlers[check_id](rule)
        weight = rule.get("weight", 0)
        score = weight if passed else 0
        total_score += score
        required = bool(rule.get("required", False))
        required_passed = required_passed and (passed or not required)
        checks[check_id] = {"passed": passed, "score": score, "weight": weight, "required": required, "reason": reason, "description": rule["description"]}
    passed = required_passed and total_score >= rubric["minimumScore"]
    return {"path": str(chapter_path), "exists": True, "score": total_score, "passed": passed, "manualReviewRequired": bool(rubric.get("manualReviewRequired", True)), "checks": checks, "wordCount": word_count}


def write_qc_report(project_dir: Path, plan: dict[str, Any], results: list[dict[str, Any]], rubric: dict[str, Any], naming_warnings: list[str]) -> Path:
    try:
        display_path = project_dir.relative_to(ROOT_DIR)
    except ValueError:
        display_path = project_dir
    lines = [
        f"# {plan['novelName']} QC 校验报告",
        "",
        "## 项目概览",
        f"- 项目路径：`{display_path}`",
        f"- 写作模式：`{plan['mode']}`",
        f"- 自动基线通过分：`{rubric['minimumScore']}`",
        "- 人工内容复核：仍需要；自动评分不等同于文学质量。",
        f"- 校验时间：`{now_iso()}`",
        "",
        "## 命名审计",
    ]
    lines.extend(f"- 警告：{warning}" for warning in naming_warnings)
    if not naming_warnings:
        lines.append("- 无命名警告")
    lines.extend(["", "## 章节结果", "", "| 章节 | 自动基线 | 字数 | 评分 | 未通过项 |", "|------|----------|------|------|----------|"])
    for chapter, result in zip(plan["chapters"], results):
        failed_checks = [check["description"] for check in result["checks"].values() if not check["passed"]]
        lines.append(f"| 第{chapter['chapterNumber']:02d}章 | {'通过' if result['passed'] else '未通过'} | {result['wordCount']} | {result['score']} | {'；'.join(failed_checks) if failed_checks else '无'} |")
    lines.extend(["", "## 详细原因", ""])
    for chapter, result in zip(plan["chapters"], results):
        lines.append(f"### 第{chapter['chapterNumber']:02d}章：{chapter['title']}")
        for check_id, check in result["checks"].items():
            marker = "PASS" if check["passed"] else "FAIL"
            requirement = "必需" if check["required"] else "参考"
            lines.append(f"- `{check_id}` [{marker}/{requirement}] {check['reason']}")
        lines.append("")
    report_path = project_dir / "QC校验报告.md"
    atomic_write_text(report_path, "\n".join(lines).rstrip() + "\n")
    return report_path


def validate_project(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    plan_path = find_plan_file(project_dir)
    with plan_lock(plan_path):
        _, plan = load_plan(project_dir)
        _, naming_warnings = validate_plan_data(plan)
        rubric = load_rubric()
        results = []
        plan["status"] = "validating"
        for chapter in plan["chapters"]:
            result = evaluate_chapter(project_dir / chapter["filePath"], plan["minWordsPerChapter"], plan["maxWordsPerChapter"], rubric)
            chapter["wordCount"] = result["wordCount"]
            chapter["wordCountPass"] = result["checks"]["word_count"]["passed"]
            chapter["validation"] = {"score": result["score"], "passed": result["passed"], "manualReviewRequired": result["manualReviewRequired"], "checks": result["checks"]}
            chapter["status"] = "completed" if result["passed"] else "failed"
            if not result["passed"]:
                chapter["retryCount"] = int(chapter.get("retryCount", 0)) + 1
            results.append(result)
        plan["status"] = "completed" if results and all(item["passed"] for item in results) else "failed"
        plan["updatedAt"] = now_iso()
        plan["namingValidation"] = {"warnings": naming_warnings, "checkedAt": now_iso()}
        save_json(plan_path, plan)
        report_path = write_qc_report(project_dir, plan, results, rubric, naming_warnings)
    passed_count = sum(1 for item in results if item["passed"])
    print(f"校验完成: {passed_count}/{len(results)} 章通过自动基线")
    print(f"计划状态: {plan['status']}")
    print("提示: 自动基线通过后仍需人工复核内容一致性与原创性。")
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
    status_parser.add_argument("--project-status", choices=sorted(PROJECT_STATUSES))
    status_parser.add_argument("--chapter", type=int)
    status_parser.add_argument("--chapter-status", choices=sorted(CHAPTER_STATUSES))
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
    try:
        return args.func(args)
    except (FileNotFoundError, FileExistsError, ValueError, json.JSONDecodeError, TimeoutError) as error:
        print(f"错误: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
