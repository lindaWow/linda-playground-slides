# Linda Playground slides

把提纲、课程、演讲、分享材料和长文，转化为富含实验排版、鲜明撞色、动态字体、组件互动与滚动叙事的交互式 HTML 演示。

它会帮助 AI 完成内容提炼、页面编排、动效选择、渐进式信息披露、桌面与手机适配，以及字体和资源内置的单文件导出。

## 适合制作

- 交互式 Slides 与网页 PPT
- 滚动叙事演示和演讲型微型网站
- 课程、发布会与作品展示
- 文字驱动的数字展览
- 需要强烈视觉节奏和实验排版的单页体验

## 安装为 Plugin

在 Codex 中添加这个 GitHub Marketplace：

```bash
codex plugin marketplace add lindaWow/linda-playground-slides
codex plugin add linda-playground-slides@linda-playground-slides
```

安装后，在新对话中直接描述任务，或显式调用：

```text
$linda-playground-slides 把以下内容制作成交互式 HTML 演示……
```

## 直接安装 Skill

如果只需要 Skill，可以把 `skills/linda-playground-slides` 复制到个人的 `.agents/skills/` 目录，再在新对话中调用 `$linda-playground-slides`。

## 设计语言

- 现代主义网格与实验编辑排版
- 字体作为画面主体的 kinetic typography
- 来自限定色库的鲜明撞色与多色组合
- 组件化交互、滚动叙事和渐进式披露
- 桌面端充分占满画面，手机端重新编排信息
- 尊重 `prefers-reduced-motion`，保留可访问性与键盘操作

## 仓库结构

```text
plugin.json
.agents/plugins/marketplace.json
skills/linda-playground-slides/
├── SKILL.md
├── agents/openai.yaml
├── assets/
├── references/
└── scripts/
```

## 字体与第三方参考

仓库内置 Noto Sans SC 与 Roboto Flex 的网页字体文件，分别随附 SIL Open Font License 文本。视觉与交互参考来源记录在 `skills/linda-playground-slides/references/sources.md`；Starter、脚本和组件系统为这套 Skill 单独实现。

字体工具会在具备 `fonttools` 与 `brotli` 时生成更小的中文子集；精简运行环境会自动使用完整字体，仍可离线导出，只是单文件体积会更大。

## License

当前仓库尚未选择统一的开源许可证。内置字体继续遵循各自随附的 SIL Open Font License。
