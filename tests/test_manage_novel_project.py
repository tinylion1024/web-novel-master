from __future__ import annotations

import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import manage_novel_project as manager


def make_args(**overrides: object) -> Namespace:
    values: dict[str, object] = {
        "mode": "professional",
        "title": "测试小说",
        "genre": "都市",
        "golden_finger": "系统",
        "core_tropes": "逆袭",
        "chapters": 1,
        "min_words": 2000,
        "max_words": 3000,
        "writing_mode": "serial",
        "protagonist": "许沉舟",
        "heroine": "闻棠",
        "antagonist": "赵观澜",
        "chapter_titles": [],
    }
    values.update(overrides)
    return Namespace(**values)


def valid_text() -> str:
    vocabulary = "".join(chr(0x4E00 + index) for index in range(220))
    return "危机系统打脸突破“这是一句具有完整长度的对白内容”" + vocabulary * 10 + "反击来人"


class ManageNovelProjectTests(unittest.TestCase):
    def test_build_plan_uses_v4_contract(self) -> None:
        plan = manager.build_plan(make_args(), Path("20260717-测试小说"))
        errors, warnings = manager.validate_plan_data(plan)
        self.assertEqual(plan["version"], 4)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_migrate_v3_renames_legacy_naming_field(self) -> None:
        plan = manager.build_plan(make_args(), Path("20260717-测试小说"))
        plan["version"] = 3
        plan["namingLedger"]["blockedHighFrequency"] = plan["namingLedger"].pop("defaultAvoidSurnames")
        migrated, changed = manager.migrate_plan(plan)
        errors, _ = manager.validate_plan_data(migrated)
        self.assertTrue(changed)
        self.assertEqual(migrated["version"], 4)
        self.assertIn("defaultAvoidSurnames", migrated["namingLedger"])
        self.assertEqual(errors, [])

    def test_load_plan_migrates_legacy_path_and_initializing_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory)
            plan = manager.build_plan(make_args(), Path("legacy-project"))
            plan["version"] = 1
            plan["status"] = "initializing"
            plan.pop("projectPath")
            plan.pop("writingMode")
            manager.save_json(project_dir / manager.PLAN_FILE_NAME, plan)
            _, migrated = manager.load_plan(project_dir)
        self.assertEqual(migrated["version"], 4)
        self.assertEqual(migrated["status"], "planning")
        self.assertEqual(migrated["projectPath"], f"./web-novels/{project_dir.name}")

    def test_invalid_chapter_limits_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "章节数"):
            manager.build_plan(make_args(chapters=0), Path("invalid"))
        with self.assertRaisesRegex(ValueError, "最大字数"):
            manager.build_plan(make_args(min_words=3000, max_words=2000), Path("invalid"))

    def test_duplicate_names_fail_and_high_frequency_names_warn(self) -> None:
        plan = manager.build_plan(make_args(protagonist="林风", heroine="林风"), Path("20260717-测试小说"))
        errors, warnings = manager.validate_plan_data(plan)
        self.assertTrue(any("重复名称" in item for item in errors))
        self.assertTrue(any("高频姓氏" in item for item in warnings))

    def test_unsafe_chapter_path_is_rejected(self) -> None:
        plan = manager.build_plan(make_args(), Path("20260717-测试小说"))
        plan["chapters"][0]["filePath"] = "../README.md"
        errors, _ = manager.validate_plan_data(plan)
        self.assertTrue(any("安全相对路径" in item for item in errors))

    def test_repeated_placeholder_text_fails_content_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            chapter_path = Path(directory) / "第01章.md"
            chapter_path.write_text("# 第01章\n" + "危机打脸" * 500, encoding="utf-8")
            result = manager.evaluate_chapter(chapter_path, 2000, 3000, manager.load_rubric())
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["content_integrity"]["passed"])

    def test_complete_baseline_text_passes_but_requires_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            chapter_path = Path(directory) / "第01章.md"
            chapter_path.write_text("# 第01章\n" + valid_text(), encoding="utf-8")
            result = manager.evaluate_chapter(chapter_path, 2000, 3000, manager.load_rubric())
        self.assertTrue(result["passed"])
        self.assertTrue(result["manualReviewRequired"])

    def test_atomic_json_write_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            payload = {"title": "测试", "value": 1}
            manager.save_json(path, payload)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), payload)

    def test_validate_project_writes_a_completed_v4_plan_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_dir = Path(directory)
            plan = manager.build_plan(make_args(), Path("20260717-测试小说"))
            manager.save_json(project_dir / manager.PLAN_FILE_NAME, plan)
            chapter_path = project_dir / "chapters" / "第01章.md"
            chapter_path.parent.mkdir()
            chapter_path.write_text("# 第01章\n" + valid_text(), encoding="utf-8")
            exit_code = manager.validate_project(Namespace(project_dir=str(project_dir)))
            updated = json.loads((project_dir / manager.PLAN_FILE_NAME).read_text(encoding="utf-8"))
            report = (project_dir / "QC校验报告.md").read_text(encoding="utf-8")
        self.assertEqual(exit_code, 0)
        self.assertEqual(updated["status"], "completed")
        self.assertEqual(updated["version"], 4)
        self.assertIn("人工内容复核", report)

    def test_status_transitions_are_constrained(self) -> None:
        with self.assertRaisesRegex(ValueError, "不能从 completed 变为 in_progress"):
            manager.ensure_transition("completed", "in_progress", manager.PROJECT_TRANSITIONS, "项目")


if __name__ == "__main__":
    unittest.main()
