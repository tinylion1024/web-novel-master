#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档一致性校验工具。

校验项：
1. Markdown 本地链接是否存在
2. 路径大小写是否与磁盘一致
3. 技能入口是否包含四种模式的真实入口文件
4. 是否仍残留已禁用的旧路径/旧命名
"""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MARKDOWN_GLOBS = [
    "*.md",
    "examples/**/*.md",
    "references/**/*.md",
]

EXPECTED_MODE_ENTRIES = [
    "references/flows/Fast/Fast0_Initialization.md",
    "references/flows/Pro/Pro0_Initialization.md",
    "references/flows/Ind/Ind0_Project_Initialize.md",
    "references/flows/Instant/Instant0_One_Shot.md",
]
PLAN_SCHEMA_PATH = ROOT_DIR / "schemas" / "writing-plan.schema.json"
RUBRIC_PATH = ROOT_DIR / "references" / "Check" / "Quality-Rubric.json"

BANNED_PATTERNS = {
    "references/Flow/": "旧目录名，应使用 references/flows/",
    "05-写作计划.json": "写作计划统一为 03-写作计划.json",
    "第XX章-标题.md": "章节文件统一为 chapters/第01章.md 形式",
}


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for pattern in MARKDOWN_GLOBS:
        files.extend(sorted(ROOT_DIR.glob(pattern)))
    return files


def exact_path_exists(path: Path) -> bool:
    if path == ROOT_DIR:
        return True
    try:
        relative = path.relative_to(ROOT_DIR)
    except ValueError:
        return False

    current = ROOT_DIR
    for part in relative.parts:
        matches = {item.name: item for item in current.iterdir()}
        if part not in matches:
            return False
        current = matches[part]
    return current.exists()


def resolve_local_link(source: Path, target: str) -> Path:
    target_path = target.split("#", 1)[0]
    return (source.parent / target_path).resolve()


def find_link_errors(file_path: Path) -> list[str]:
    errors: list[str] = []
    text = file_path.read_text(encoding="utf-8")
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1).strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        resolved = resolve_local_link(file_path, target)
        if not exact_path_exists(resolved):
            errors.append(f"{file_path.relative_to(ROOT_DIR)} -> 缺失链接目标: {target}")
    return errors


def find_banned_pattern_errors(file_path: Path) -> list[str]:
    errors: list[str] = []
    text = file_path.read_text(encoding="utf-8")
    for pattern, message in BANNED_PATTERNS.items():
        if pattern in text:
            errors.append(f"{file_path.relative_to(ROOT_DIR)} -> {message}: {pattern}")
    return errors


def validate_skill_entries(skill_path: Path) -> list[str]:
    text = skill_path.read_text(encoding="utf-8")
    errors = []
    for entry in EXPECTED_MODE_ENTRIES:
        if entry not in text:
            errors.append(f"{skill_path.relative_to(ROOT_DIR)} -> 缺少模式入口: {entry}")
    return errors


def validate_machine_contracts() -> list[str]:
    errors: list[str] = []
    try:
        schema = json.loads(PLAN_SCHEMA_PATH.read_text(encoding="utf-8"))
        if schema.get("properties", {}).get("version", {}).get("const") != 4:
            errors.append("schemas/writing-plan.schema.json -> version 必须固定为 4")
        required = set(schema.get("required", []))
        for field in ("namingLedger", "chapters", "writingMode"):
            if field not in required:
                errors.append(f"schemas/writing-plan.schema.json -> 缺少必填字段: {field}")
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"schemas/writing-plan.schema.json -> 无法读取: {error}")

    try:
        rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        check_ids = {item.get("id") for item in rubric.get("checks", []) if isinstance(item, dict)}
        if rubric.get("version") != 2:
            errors.append("references/Check/Quality-Rubric.json -> version 必须为 2")
        if not rubric.get("manualReviewRequired"):
            errors.append("references/Check/Quality-Rubric.json -> 必须要求人工内容复核")
        for check_id in ("word_count", "content_integrity"):
            if check_id not in check_ids:
                errors.append(f"references/Check/Quality-Rubric.json -> 缺少校验项: {check_id}")
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"references/Check/Quality-Rubric.json -> 无法读取: {error}")
    return errors


def main() -> int:
    files = iter_markdown_files()
    errors: list[str] = []

    for file_path in files:
        errors.extend(find_link_errors(file_path))
        errors.extend(find_banned_pattern_errors(file_path))

    errors.extend(validate_skill_entries(ROOT_DIR / "SKILL.md"))
    errors.extend(validate_machine_contracts())

    if errors:
        print("文档校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"文档校验通过，共检查 {len(files)} 个 Markdown 文件。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
