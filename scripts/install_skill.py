#!/usr/bin/env python3
"""Install Web Novel Master into a supported local skill directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_NAME = "web-novel-master"
DEFAULT_TARGETS = {
    "claude-code": Path.home() / ".claude" / "skills",
    "openclaw": Path.home() / ".openclaw" / "skills",
}
EXCLUDED_NAMES = {".claude", ".git", ".github", ".omx", "__pycache__", "tests", "web-novels"}


def default_target(platform: str) -> Path:
    return DEFAULT_TARGETS[platform]


def ignore_unneeded_files(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in EXCLUDED_NAMES or name == ".DS_Store"}


def install_skill(source: Path, target_root: Path, *, force: bool = False, dry_run: bool = False) -> Path:
    source = source.resolve()
    destination = target_root.expanduser() / SKILL_NAME
    if not (source / "SKILL.md").is_file():
        raise ValueError(f"技能源目录缺少 SKILL.md: {source}")
    if destination.resolve() == source:
        raise ValueError("目标目录不能与技能源目录相同")
    if destination.exists() and not force:
        raise FileExistsError(f"目标已存在: {destination}；如需覆盖请使用 --force")
    if dry_run:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=ignore_unneeded_files)
    if not (destination / "SKILL.md").is_file():
        raise RuntimeError("安装后未找到 SKILL.md")
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="安装 Web Novel Master 技能")
    parser.add_argument("--platform", choices=sorted(DEFAULT_TARGETS), default="claude-code")
    parser.add_argument("--target", type=Path, help="覆盖默认技能根目录")
    parser.add_argument("--force", action="store_true", help="覆盖同名已安装技能")
    parser.add_argument("--dry-run", action="store_true", help="仅显示目标路径，不写入文件")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_root = args.target or default_target(args.platform)
    destination = install_skill(ROOT_DIR, target_root, force=args.force, dry_run=args.dry_run)
    action = "将安装" if args.dry_run else "已安装"
    print(f"{action} {SKILL_NAME} 到: {destination}")
    if not args.dry_run:
        print("请重启或刷新对应助手会话后再调用该技能。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
