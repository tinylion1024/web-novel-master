# 安装与兼容说明

Web Novel Master 的 Python 工具需要 Python 3.11+。技能本体由仓库根目录的 `SKILL.md` 和 `references/`、`scripts/` 等同级文件组成。

## Claude Code

已验证的安装目标是用户级技能目录：

```bash
git clone https://github.com/tinylion1024/web-novel-master.git
cd web-novel-master
python3 scripts/install_skill.py --platform claude-code
```

安装器默认写入 `~/.claude/skills/web-novel-master`，不会复制本地草稿、测试、Git 元数据或 CI 配置。目标已存在时默认拒绝覆盖；确认更新时显式传入 `--force`。可先使用 `--dry-run` 查看目标路径。

重启 Claude Code 后，以 `/skill web-novel-master` 调用技能。Claude Code 本身的安装、认证和版本诊断请参考 [官方入门文档](https://docs.anthropic.com/en/docs/claude-code/getting-started)。

## OpenClaw

OpenClaw 会从配置的技能根目录下发现 `SKILL.md`。在仓库根目录执行：

```bash
openclaw skills install . --global
```

该命令安装到 OpenClaw 的共享技能目录；也可以去掉 `--global`，安装到当前工作区。安装后运行 `openclaw skills list` 检查是否已发现 `web-novel-master`。加载目录、优先级和更新行为以 [OpenClaw Skills 文档](https://docs.openclaw.ai/skills) 为准。

## 仅使用项目管理工具

不使用任何 AI 助手时，仍可运行项目初始化和 QC 基线校验：

```bash
python3 scripts/manage_novel_project.py --help
python3 scripts/manage_novel_project.py init --help
```

## 故障排查

| 现象 | 检查方式 |
|---|---|
| 安装器提示目标已存在 | 使用 `--dry-run` 确认路径；只有确认覆盖时才添加 `--force`。 |
| 助手找不到技能 | 确认安装目录下存在 `web-novel-master/SKILL.md`，然后重启或刷新会话。 |
| OpenClaw 未发现技能 | 执行 `openclaw skills list`，检查安装范围与配置的技能根目录。 |
| Python 工具运行失败 | 执行 `python3 --version`，确保版本不低于 3.11。 |
