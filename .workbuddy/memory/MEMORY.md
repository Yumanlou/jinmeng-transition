# 晋蒙转型项目 · 长期笔记

## 项目是什么
绿色信贷（2012《绿色信贷指引》）对山西、内蒙古等煤炭暴露地区的能源转型实证研究。识别：连续暴露 DID（Post2012 × 政策前煤炭暴露 coalexp_pre），省级面板 2000–2023。

## 核心故事（一句话）
绿色信贷让高煤省"少用煤"（运行层：能源/煤炭强度下降），但逼不动它们"关电厂"（结构层：火电资本退出）。行政淘汰停了、金融替代没接上，出现"退出真空"。

## 理论框架（四层）
1. 金融约束进入：绿色信贷 → 转型金融谱系
2. 分层调整（核心）：运行性→构成性→结构替代（调整成本+资产不可逆性推导时序）
3. 地方禀赋与吸收能力：调节各层速度
4. 转型融资设计：能效融资→转型贷款→退出/搁浅资产处置（理论出口）

## 文献定位（重要）
接到"转型金融 + 公正转型 + 搁浅资产"线，不是"绿色信贷效果评估"线。理由：绿色信贷线太挤、且本文定位是"分层事实+边界"非强因果；转型金融线政策热、学术实证滞后、区域层空白。锚点：OECD 2019、Tandon 2021、马骏 2025、周小川 2025、Caldecott 2013、Davidson et al 2024。

## 关键实证（证据强度递减）
- 运行层（能源/煤炭强度）：baseline 显著，竞争解释稳健，处理强度×趋势（c.coalexp_pre#c.year）下仍显著（coalterm_int p=0.04、energy5_int p=0.025）；但省份固定趋势、早期窗口下失效 → 效应是"渐进启动"型。
- 构成层（煤炭占比）：baseline 显著，趋势下弱，事件研究 2013 后才转负。
- 结构层（火电）：GEM 机组级左截断 Cox，高煤省退役 hazard 比 政策前 4.79***（上大压小）→ 2012 后 1.23 不显著 → 1.49（供给侧）→ 2.62（双碳）。= 结构替代"相对放缓"的 2012 断点（已写入 .tex）。
- 污染（SO2/NOx/固废）：不稳健，不写主文。

## 数据资产
- 主面板：data/final_data...0721.csv（744 obs，710 vars）
- Wind EDB（0820 新取）：data/wind_edb/（全国绿色贷款、31省贷款余额 5940 行、31省工业增加值 5386 行，月频 2009–2024）
- GEM 机组：data/gem_power_project_lifecycle/gem_china_project_units_2026_snapshot.csv（煤电 4326 机组）
- 论文：output/paper_revised_cn_0718.tex（中）、paper_submission_en_0718.tex（英）

## 工具/环境约定
- Stata：/Applications/Stata/StataMP.app/Contents/MacOS/StataMP -b do xxx.do
- Python venv：~/.workbuddy/binaries/python/envs/default（已装 numpy/pandas/scipy/lifelines）
- Wind 数据：走 skill CLI（cd ~/.agents/skills/wind-mcp-skill/ && node scripts/cli.mjs call ...），**不走 connector**。Key 在 ~/.wind-aifinmarket/config。
- 论文格式：发表物纯黑白、宋体、顿号分隔符（、）。

## 待办
- 分省分行业信贷（高耗能行业贷款）：Wind EDB 没有，需 Wind 终端/CSMAR（第一层金融约束直接证据）
- 跨省输电/外送通道：中电联/年鉴（第三层）
- 英文版期刊定位：见 energy/environment 类（Energy Economics、Energy Policy、Resource and Energy Economics 等），需复核
