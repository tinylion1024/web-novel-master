# 发布指南

每次公开版本应包含可理解的变更说明和可复现的验证结果。

## 发布前

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_docs.py
git diff --check
```

确认 `CHANGELOG.md` 已记录用户可见的变更，并检查示例、资料和发布说明不含未授权文本或私人草稿。

## 创建版本

1. 将版本号更新到 README 徽章和 `CHANGELOG.md`。
2. 提交并推送 `main`。
3. 使用 `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file docs/releases/vX.Y.Z.md` 创建 Release。
4. 回读 Release 页面，确认标题、标签、说明和下载资源正确。

不要把用户小说、环境配置、密钥或运行日志附加到 Release。
