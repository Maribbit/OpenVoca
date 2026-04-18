<p align="right">
  <a href="./README.md">English</a> | 中文
</p>

<br />

<p align="center">
  <img src="./logo.svg" width="140" height="140" alt="OpenVoca" />
</p>

<h1 align="center">OpenVoca</h1>

<p align="center">
  <em>在阅读中自然积累词汇。</em>
</p>

<p align="center">
  一个极简的、基于 LLM 的英语词汇工具——<br />
  通过阅读 AI 生成的上下文例句来学习新单词。
</p>

<br />

![演示](./demo.gif)

## OpenVoca 是什么？

OpenVoca 通过阅读帮助你积累英语词汇。不再孤立地背单词卡，而是阅读由 AI 生成的短文——这些句子会自然地融入你需要练习的单词。

**工作流程：**

1. **阅读** — AI 生成一个包含目标词汇的句子。
2. **划词** — 点击句子中不认识的单词，将其加入词库。
3. **迭代** — 系统追踪每个单词的熟悉度，在合适的时机让它重新出现。

经过多轮练习，你的词汇量会通过有意义的上下文自然增长，而不是死记硬背。间隔重复算法确保你不熟悉的单词出现得更频繁，已掌握的单词则逐渐淡出。

OpenVoca 完全本地运行，数据不会离开你的设备。你需要自备 LLM 端点（Ollama、OpenRouter、Groq、硅基流动，或任何兼容 OpenAI API 的服务）。

---

## 架构

OpenVoca 是一个包含前后端的 monorepo。

- **前端**：Vue 3 + TypeScript + Vite + Tailwind CSS v4
  *详见 [frontend/README.md](./frontend/README.md)*
- **后端**：Python 3.12+（由 uv 管理）+ FastAPI + SQLModel + SQLite
  *详见 [backend/README.md](./backend/README.md)*

## 测试

本项目遵循测试驱动开发（TDD）：
- **前端**：在 `frontend/` 目录运行 `pnpm run check`
- **后端**：在 `backend/` 目录运行 `uv run ruff format --check .; uv run ruff check .; uv run pytest`
- **全部**：VS Code 任务 `✅ Check OpenVoca (All)`

## 构建发布包

```bash
uv run python scripts/bundle.py
```

生成 `dist/openvoca-{version}-win-x64.zip`——一个无需安装的 Windows 便携包。详见 `scripts/bundle.py`。

## 版本与贡献

- **版本**：仓库根目录的 `VERSION` 为唯一版本源
- **贡献指南**：见 [CONTRIBUTING.md](./CONTRIBUTING.md)
- **发布指南**：见 [RELEASE.md](./RELEASE.md)

## 许可证

Copyright (C) 2026 OpenVoca Contributors

基于 [GNU Affero 通用公共许可证 v3.0](LICENSE)（AGPL-3.0）授权。

你可以在 AGPL-3.0 条款下自由使用、修改和分发本软件。任何修改版本在分发或作为网络服务运行时，也必须以 AGPL-3.0 发布并提供源代码。

允许商业使用，但须遵守 AGPL-3.0 条款。

内置词典数据来源于 [ECDICT](https://github.com/skywind3000/ECDICT)，基于 MIT 许可证。
