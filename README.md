# Bloom Learning Skill

`Bloom Learning` 是一个面向 Obsidian 的本地优先学习型 skill。它把 Bloom's 2 Sigma tutoring、间隔复习、知识地图和会话持久化组合成一个可复用的学习工作流。

这个仓库把 skill 本体放在独立目录 `bloom-learning/` 下，仓库级文档放在根目录，便于发布到 GitHub，同时保持 skill 目录本身足够干净。

## Highlights

- Local-first: 学习状态、知识地图、笔记和复习计划都保存在本地 Markdown 文件中
- Obsidian-friendly: 使用普通目录结构和 `[[wikilinks]]`
- Strategy-aware: 根据概念型、程序型、事实型、系统型、项目型内容切换不同教学策略
- Lightweight automation: 提供初始化脚本和间隔复习脚本

## Repository Structure

```text
.
├── README.md
├── .gitignore
├── docs/
│   └── improvement-design-proposal.md
└── bloom-learning/
    ├── SKILL.md
    ├── assets/
    ├── references/
    └── scripts/
```

## Quick Start

1. 将 `bloom-learning/` 目录复制或链接到你的 `$CODEX_HOME/skills/` 下。
2. 在支持 skills 的环境中引用 `bloom-learning`。
3. 初始化一个学习主题：

```bash
bash bloom-learning/scripts/init-vault.sh "/path/to/Obsidian Vault" "Python 装饰器" beginner
```

4. 检查到期复习项：

```bash
python3 bloom-learning/scripts/review-check.py "/path/to/topic/_meta/spaced-repetition.md"
```

## What Is Included

- [`bloom-learning/SKILL.md`](./bloom-learning/SKILL.md): skill 主说明
- `bloom-learning/assets/templates/`: 初始化模板
- `bloom-learning/references/`: 教学策略与 SM-2 参考资料
- `bloom-learning/scripts/`: 初始化与复习检查脚本
- [`docs/improvement-design-proposal.md`](./docs/improvement-design-proposal.md): 下一版改进提案

## Current Limitations

- 复习脚本依赖英文表头与标题，国际化支持偏弱
- `Mastered` 状态的迁移动作目前没有完全自动化
- 多数 session 持久化仍依赖 agent 手工维护多个 Markdown 文件
- 初始化脚本对特殊字符 topic 的健壮性还不够

## Roadmap

建议先按 [`docs/improvement-design-proposal.md`](./docs/improvement-design-proposal.md) 做增量改进，再考虑重构 skill 的状态层。
