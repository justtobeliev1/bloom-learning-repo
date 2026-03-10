# Bloom Learning Skill 改进设计提案

## 目标

在不破坏当前使用方式的前提下，把 `bloom-learning` 从“依赖 agent 自觉遵守的 workflow”升级成“有明确状态模型、可验证、可迁移的学习系统”。

## 当前问题

1. 初始化脚本对 topic 名称中的特殊字符不安全。
2. `spaced-repetition.md` 的 `Mastered` 规则写在设计里，但没有在脚本里完全落地。
3. 脚本依赖固定英文标题和列名，和“跟随学习者语言”这个目标冲突。
4. `progress.md`、`knowledge-map.md`、`notes/` 的更新流程缺少统一入口，长期容易漂移。
5. 状态主要嵌在自然语言文本中，对自动化脚本不友好。

## 设计原则

- Human-readable first: 继续以 Markdown 为主，不引入重型数据库
- Machine-safe second: 关键状态必须有稳定的结构化表示
- Incremental migration: 允许旧目录结构继续工作
- Language decoupling: 展示语言和机器解析协议分离

## 提案概览

### 1. 引入结构化状态层

保留现有 Markdown 文件，但在 `_meta/` 下增加一个机器可读状态文件，例如：

```text
_meta/
├── progress.md
├── knowledge-map.md
├── spaced-repetition.md
└── state.json
```

`state.json` 负责保存：

- 当前 module / concept
- 已掌握概念列表
- session 计数
- 每个 concept 的复习参数
- learner profile（level、pace、偏好）

这样脚本读写稳定状态，Markdown 主要承担展示和人工编辑角色。

### 2. 把 session 更新收敛到单一入口

新增一个统一脚本，例如：

```text
bloom-learning/scripts/session-commit.py
```

它负责一次性完成：

- 追加 `progress.md` session log
- 更新 `knowledge-map.md` 复选框
- 更新 `spaced-repetition.md`
- 为新概念生成或更新 `notes/*.md`
- 同步 `state.json`

这样 skill 的“Always persist state to files”就不再只是约定，而是可执行能力。

### 3. 重做 spaced repetition 的状态机

建议把复习项明确分成三种状态：

- `due`
- `scheduled`
- `mastered`

规则：

- 复习正确后重新计算 `interval` 和 `ease`
- 当 `interval > 30` 时，从 `due` 自动迁移到 `mastered`
- `mastered` 项保留历史，但不再混在待复习列表里

`review-check.py` 可以拆成两个职责明确的命令：

- `review-due`: 列出待复习项
- `review-apply`: 写回复习结果并迁移状态

### 4. 让模板与解析协议解耦

不要让脚本依赖英文标题 `## Due for Review` 或列名 `Next review`。更稳妥的方式有两种：

1. 在 Markdown 中使用隐藏标记，例如 HTML comments
2. 只让脚本读 `state.json`，Markdown 表格只做渲染输出

推荐第二种。这样展示内容可以是中文、英文或双语，脚本都不受影响。

### 5. 初始化流程安全化

`init-vault.sh` 需要：

- 正确转义 topic / level 内容
- 对非法路径字符做规范化处理
- 支持 `--resume` 或显式区分“新建”和“恢复”
- 在初始化后生成一个最小可运行的知识地图骨架

## 推荐的版本化落地顺序

### v1.1

- 修复 `init-vault.sh` 特殊字符替换问题
- 修复 `review-check.py` 的 `Mastered` 迁移
- 增加 `.md` 文件格式约束说明

### v1.2

- 引入 `state.json`
- 增加 `session-commit.py`
- 让 `review-check.py` 改为优先读写结构化状态

### v2.0

- 完整支持多语言展示
- 支持 learner profile 与节奏自适应
- 支持项目型学习的 milestone 跟踪

## 建议保留的部分

以下设计不建议推翻：

- Bloom 2 Sigma + SM-2 的组合方向
- Obsidian 本地 Markdown 持久化
- 按内容类型切换教学策略
- `notes / exercises / summaries / projects` 这套目录结构

## 结论

这个 skill 的核心价值不是脚本本身，而是把教学策略、知识管理和复习调度串成一个统一工作流。下一步最值得做的，不是继续堆提示词，而是把“状态层”和“写回路径”做扎实。
