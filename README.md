<div align="center">

# 🌱 Bloom Learning

**让 AI 像最好的私人导师一样教你任何东西**

*基于 Bloom 2-Sigma 理论 · 本地 Obsidian 知识库 · 间隔复习自动化*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

</div>

---

## 💡 一句话介绍

教育心理学家 Benjamin Bloom 在 1984 年发现：**一对一辅导的学生比传统课堂学生高出两个标准差** — 这就是著名的 *2 Sigma Problem*。

Bloom Learning 把这个理论变成了一个可运行的 AI Skill：它会根据你正在学的内容**自动切换教学策略**，用间隔复习帮你**对抗遗忘曲线**，并把所有学习进度保存在你自己的 Obsidian 笔记库里 — 没有云端，没有订阅，**你的知识永远属于你**。

## ✨ 它能做什么

| 能力 | 说明 |
|------|------|
| 🎯 **自适应教学** | 概念理解用苏格拉底提问，动手技能用引导练习，事实记忆用直接教学… 5 种策略自动匹配 |
| 🧠 **间隔复习** | 内置 SM-2 算法，自动追踪每个知识点的复习时间，不让你白学 |
| 🗺️ **知识地图** | 自动生成学习路线图，勾选已掌握内容，一眼看清进度 |
| 📝 **Obsidian 原生** | 所有数据都是 Markdown + JSON，支持 `[[wikilinks]]`，和你现有的笔记无缝共存 |
| 💾 **会话持久化** | 每次学习结束自动保存进度，下次打开无缝继续 |

## 🚀 快速开始

### 1. 安装

将 `bloom-learning/` 目录复制（或软链接）到你的 Skills 目录下：

```bash
cp -r bloom-learning/ "$CODEX_HOME/skills/bloom-learning"
```

### 2. 开始学习一个新主题

```bash
bash bloom-learning/scripts/init-vault.sh "/你的/Obsidian笔记库" "Python 装饰器" beginner
```

这会在你的笔记库里创建如下结构：

```
Python 装饰器/
├── _meta/
│   ├── progress.md          # 学习进度和会话历史
│   ├── knowledge-map.md     # 知识地图（带 ✅ 掌握状态）
│   ├── spaced-repetition.md # 间隔复习计划
│   └── state.json           # 机器可读的状态源
├── notes/                   # 每个知识点的笔记
├── exercises/               # 练习题
├── summaries/               # 你写的总结
└── projects/                # 实战项目
```

### 3. 检查今天该复习什么

```bash
python3 bloom-learning/scripts/review-check.py "/你的/笔记库/Python 装饰器/_meta/spaced-repetition.md"
```

### 4. 保存学习进度

一次学习结束后，运行以下命令把进度写回笔记库：

```bash
python3 bloom-learning/scripts/session-commit.py "/你的/笔记库/Python 装饰器" \
  --payload '{"module":"Module 1","concept":"闭包","session_summary":"理解了闭包的作用域链", ...}'
```

> 💡 **提示**：在支持 Skills 的 AI 环境中使用时，这些脚本会被自动调用，你不需要手动操作。

## 🧩 项目结构

```
bloom-learning-repo/
├── bloom-learning/            ← Skill 本体（复制这个目录即可使用）
│   ├── SKILL.md               # Skill 完整说明与教学协议
│   ├── scripts/               # 自动化脚本
│   │   ├── init-vault.sh      #   初始化学习目录
│   │   ├── review-check.py    #   复习检查 & SM-2 更新
│   │   ├── session-commit.py  #   会话持久化
│   │   └── learning_state.py  #   共享状态工具库
│   ├── assets/templates/      # 初始化模板文件
│   └── references/            # 教学策略 & SM-2 算法参考
├── docs/
│   └── improvement-design-proposal.md  # 下一版改进设计
├── LICENSE
└── README.md
```

## 🎓 教学策略一览

Bloom Learning **不会用一种方式教所有东西**。它会根据内容类型自动选择最合适的教学方法：

| 你在学什么 | AI 怎么教 | 举个例子 |
|-----------|----------|---------|
| 概念理解 | 苏格拉底式提问，引导你自己发现答案 | "闭包是什么？为什么需要它？" |
| 动手技能 | 给你一个略超当前水平的问题，然后逐步引导 | "写一个装饰器来计时函数执行" |
| 事实记忆 | 简洁讲解 + 立即测试 + 加入复习队列 | API 参数、公式、术语 |
| 系统理解 | 先给全局地图，再逐层深入 | "HTTP 请求从浏览器到服务器经历了什么？" |
| 创造应用 | 一起定义目标，拆分里程碑，教练式陪伴 | "用 Flask 搭建一个博客" |

> 更多细节见 [`references/teaching-strategies.md`](./bloom-learning/references/teaching-strategies.md)

## 🔬 间隔复习怎么工作

采用经典的 **SM-2 算法**：

- ✅ 回忆正确 → 复习间隔增长（1天 → 3天 → 按 ease 系数倍增）
- ❌ 回忆失败 → 间隔重置为 1 天，ease 系数下降
- 🎯 Ease 系数范围 1.3 ~ 3.0（默认 2.5）
- 🏆 间隔超过 30 天 → 标记为「已掌握」

> 详细算法说明和示例见 [`references/sm2-algorithm.md`](./bloom-learning/references/sm2-algorithm.md)

## ⚠️ 已知限制

- 复习脚本的表头和标题暂时依赖英文格式，国际化支持有限
- 知识地图中的自动勾选依赖 concept 名称精确匹配
- `state.json` 已是状态源，但细粒度的学习者画像还未完全启用
- 尚无自动化测试套件，验证主要靠手工回归

## 🗺️ Roadmap

我们正在按 [改进设计提案](./docs/improvement-design-proposal.md) 推进迭代。欢迎翻阅并提出想法！

---

<div align="center">
<sub>
Built with ❤️ for lifelong learners — 让每个人都能享受一对一辅导的学习效果。
</sub>
</div>
