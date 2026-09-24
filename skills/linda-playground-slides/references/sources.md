# 来源与借鉴边界

## 设计参考

- 原站：https://exat.hottype.co/ 。限定色库取自主主题样式 `:root` 的 12 个 token，参考其字体主导的布局、几何结构、色块、交互字形与阅读节奏。
- 创作者案例说明：https://tympanus.net/codrops/2026/04/10/the-exat-microsite-pushing-a-typography-showcase-to-new-creative-extremes/ 。用于核对光标距离字阵、单轴字体比较、滚动速度数字波、叠页和移动端简化等机制。
- 补充 3D 标签参考：https://tympanus.net/Tutorials/3DTextScroll/index.html ，Demo 1。将其旋转文字空间关系转化为可读的经历/类别标签组件。

区分来源：动效目录的 `E` 表示 EXAT 观察/创作者说明中的机制；`C` 表示补充 Codrops 3D 文字参考；`P` 表示本项目迭代抽象出的实现方向。不要声称所有配套效果都直接来自 EXAT。

提取规则并独立实现。不要复制原站完整源代码、商用字体文件、品牌文字、音频或插画。附带运行时为本 Skill 的独立实现，视觉机制可按内容重新组合。

## 字体

附带 OFL 字体用于可变字体与离线输出：

- Roboto Flex 项目：https://github.com/googlefonts/roboto-flex 。此处保存 Latin 字符集的可变 WOFF2，包含 `wght / wdth / opsz` 轴；完整字符覆盖以实际字体 cmap 为准。
- Noto Sans SC：https://github.com/notofonts/noto-cjk 。此处保存支持 `wght` 轴的完整来源字体，交付时按内容生成子集。不要把某次项目的中文子集当作未来任意文字的完整字体。

许可证位于 `assets/fonts/RobotoFlex-OFL.txt` 与 `assets/fonts/NotoSansSC-OFL.txt`；导出时一并内嵌。生成的中文子集会使用独立 family 名称，并保留授权信息。所需字形超出附带字体时，取得支持该字符的可分发字体，再追加或替换字体；不得静默删除文字。
