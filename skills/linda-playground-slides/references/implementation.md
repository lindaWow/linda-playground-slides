# 使用组件、字体与单文件导出

## 生成起点

将 `<skill-root>` 替换为本 Skill 的实际目录。不要把安装时的绝对目录写入网页。

```bash
python <skill-root>/scripts/scaffold.py /absolute/output/project
```

目录必须为空。脚本复制通用示例 HTML、CSS、JS 和本地字体；不会覆盖已有项目。示例展示组件能力，交付前替换全部示例内容、标题、目录和详情，删除不用的组件。默认入口 `index.html`。

用已有项目时，按需移植机制与样式；不要把整个网站套进 starter。框架项目仍可使用原工具链，最终离线导出前将依赖预打包。

## 组件接口

| 接口 | 必要结构 / 行为 |
| --- | --- |
| `data-scene` + 唯一 `id` | 观察场景可见性，建立稳定阅读锚点；`.scene` 负责空间布局 |
| `data-surface="pink"` | 使用色库 token，自动选择黑/白中对比更好的前景 |
| `data-hover-surface="green"` | 与 `.tile` 配合；hover 和键盘焦点同步切换前景/背景 |
| `data-split="reveal"` 或 `fold` | 只用于短标题；保留语义副本，逐字视觉层对辅助技术隐藏，保留 `<br>` |
| `data-type-lab` | 内含 `data-type-sample`、`input[data-axis]`、`output[data-axis-output]`；轴可用 wght/wdth/opsz，按字体能力删减 |
| `.axis-word` | 所在链接 hover/focus 时做单轴字重变化 |
| `data-glyph-field="Aa"` | 装饰字阵；设置唯一 id，配 `button[data-field-toggle="id"]` 提供触控操作 |
| `data-ring` | 内含 `.ring-source` 真实列表；自动生成装饰 3D 副本，触控/减少运动使用列表 |
| `data-velocity` | 一个短行的轻微滚动速度倾斜；停止滚动即复位 |
| `.outline-swap` | 轮廓/实心切换；可交互元素须可聚焦，不能只靠此传达状态 |
| `.reveal-grid > .tile` | 错峰入场，最终稳定对齐；任意数量可用，配色重新检查 |
| `data-magnetic` | 外层可点击，内层 `data-magnetic-inner` 轻微移动 |
| `data-tilt` | 界面框轻微透视；不要与其他 transform 动画用在同一个元素 |
| `.rotor` | 几何 SVG 旋转，只在可见场景运行 |
| `.marquee > .marquee-track` | 内部两份等宽装饰内容，无缝滚动；必须有 `data-motion-toggle` 暂停按钮 |
| `.process` | 内含指向真实章节 id 的链接；节点随屏幕重排 |
| `button[data-open="dialog-id"]` | 打开带 accessible name 的原生 dialog；关闭后恢复焦点 |
| `.fold-panel` | 原生 details/summary，不依赖 JS 阅读 |
| `data-chat-demo` | form，内含 `[name="idea"]`、`data-preview-text`、`data-demo-status`；仅本地文字预览 |
| `data-motion-toggle` | 可见的暂停/继续按钮；不隐藏内容或关闭普通交互 |

背景自动选前景只解决基础对比。色库中的鲜红底配黑色小字仍可能不足 4.5:1，starter 为对应 tile 的小字加了暖白底。更复杂正文应放在合适的中性阅读面板；不要把大字可用的组合直接套到密集正文。

外部脚本需在标记之后运行。starter 的脚本使用 `defer`；导出工具会把所有经典脚本按原始顺序放到 body 末尾，以保持 DOM 与依赖初始化顺序。

## 最小场景片段

```html
<section class="scene" id="direction" data-scene data-surface="pink">
  <div class="eyebrow"><span>02 / 项目方向</span><a href="#overview">返回总览</a></div>
  <h2 class="display compact" data-split="fold">先找到值得做的问题。</h2>
  <p class="lede">保留一个明确问题，和一个值得尝试的方向。</p>
  <button class="button" type="button" data-open="questions">7 个起点问题</button>
</section>
<dialog id="questions" aria-labelledby="questions-title">
  <div class="dialog-top"><span>起点问题</span><form method="dialog"><button class="button">关闭</button></form></div>
  <div class="dialog-content"><h2 id="questions-title">从日常摩擦开始</h2><p>在这里完整保存对应问题与方法。</p></div>
</dialog>
```

示例里的 `#overview` 需要真实存在，详情标题和内容也要随材料替换。长流程可增加轻量次级目录；starter 不强制固定的五步模型。

## 选色

读取 `assets/palette.json`。用它选 token，再分配给场景和组件。它提供用户选色范围；不会自动根据 preset 改写整站颜色。选择双色时，需要同时检查 CSS 中字阵色带、装饰和交互状态，替换为所选 token，保留黑/白中性色。更新模块配色后，检查不同屏幕排列下的邻接状态。

## 字体准备

需要 Python `fonttools` 和 `brotli`；若缺失，在当前允许的 Python 环境安装后继续。不要绕过访问限制或字体授权。

```bash
python <skill-root>/scripts/prepare_fonts.py /absolute/output/project
```

扫描当前目录中的 HTML/CSS/JS/JSON/TXT；排除 fonts、dist、node_modules 和 git。包括 JS 中的界面文字、详情文本及 Unicode 转义。检查附带 Latin 与中文字体的 cmap；字体缺字时明确报错，不能静默删掉原文。

动态数据未写在源码中时，用 `--corpus /absolute/runtime-text.txt` 提供额外文字。允许用户自由输入任意语言的编辑器，不能只依靠当前文案子集；要加入该输入语言的完整字体，或明确保留系统回退。网页的固定文案必须被内嵌字体覆盖。

附带字体只覆盖其实际字符集，特殊符号、罕见汉字和 emoji 可能需要补充。可用精确 SVG 表示装饰图标，或增加可分发的补充字体。使用自备完整字体时自行核对字形与许可，并在导出时加 `--no-font-refresh`。不得把用户的重要字符改为空白来通过检查。

修改文字后重新生成；`bundle.py` 对 scaffold 项目自动刷新。中文子集生成后改用独立 family 名称，保留原始授权记录和完整许可文件。

## 单文件输出

```bash
python <skill-root>/scripts/bundle.py /absolute/output/project/index.html --out /absolute/output/story.html
python <skill-root>/scripts/audit.py /absolute/output/story.html --palette
```

支持本地样式、经典脚本、内联 style 的资源、CSS url、图片、字体、音视频及 SVG 的本地引用。外部参考链接保持可点击。资源必须先放在项目目录中；工具不会访问网络或读取项目外文件。字体许可作为 HTML 注释保存，不放进主界面。

以下情况先处理，再导出：

- ES modules / dynamic import：用项目构建工具预打包成经典 IIFE 脚本。
- async 脚本：明确依赖顺序，改为可确定的经典脚本执行方式。
- CSS @import：展开为本地样式；复杂 CSS 构建语法先编译。
- srcset：选定嵌入版本或明确构造全内嵌的响应式源；工具不会猜。
- fetch JSON / 远程图片 / CDN 库：转换为内嵌数据与本地依赖，验证断网效果。
- iframe / 实时外部服务：提供离线降级，并准确说明功能边界；不要宣称完全离线仍有真实 AI 能力。
- 动态拼接的资源路径：改为明确的 data URL、内嵌 SVG 或本地可序列化数据。

用回调处理字符串替换，避免脚本中的 `$&`、反斜线或 HTML 字符被替换引擎误解释。不要把 base64、源码、调试日志或导出说明塞进成品可见文案。

## 检查边界

`audit.py` 检查资源引用、重复 id、缺失锚点、dialog 命名、viewport、禁止缩放、JavaScript 语法与可选配色 token；对网络调用给出人工检查提示。它无法判断视觉溢出、相邻色块关系、实际字体是否正确渲染、触控和滚动体验。完成静态检查后，按 `responsive-and-navigation.md` 在浏览器验证最终输出。
