#!/usr/bin/env node

import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const fs = require("fs");
const path = require("path");
const pptxgen = require("/Users/yumanlou/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs");

const ROOT = "/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型";
const OUT = path.join(ROOT, "output", "实证结果汇报_四页 [自动保存].pptx");
const BACKUP = path.join(ROOT, "output", "实证结果汇报_四页 [自动保存].bak_before_tables.pptx");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.subject = "绿色信贷实证结果汇报";
pptx.title = "实证结果汇报";
pptx.company = "CUFE";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";

const C = {
  bg: "FFFFFF",
  ink: "32363A",
  muted: "6B7280",
  red: "07245E",
  redDark: "07245E",
  cream: "FFFFFF",
  border: "A9A9A9",
  head: "FFFFFF",
  pale: "F6F8FC",
};

function addHeader(slide, num, kicker, title, subtitle) {
  slide.background = { color: C.bg };
  slide.addShape(pptx.ShapeType.rect, { x: 0.34, y: 0.28, w: 0.05, h: 0.82, fill: { color: C.red }, line: { color: C.red } });
  slide.addShape(pptx.ShapeType.ellipse, { x: 10.7, y: -0.2, w: 2.0, h: 2.0, fill: { color: C.red }, line: { color: C.red } });
  slide.addShape(pptx.ShapeType.ellipse, { x: 11.45, y: -0.58, w: 2.1, h: 2.1, fill: { color: C.red }, line: { color: C.red } });
  slide.addText("北京外国语大学", {
    x: 11.25, y: 0.56, w: 1.65, h: 0.2, fontFace: "Microsoft YaHei", fontSize: 8.5, bold: true, color: "FFFFFF", margin: 0,
  });
  slide.addText("BEIJING FOREIGN STUDIES UNIVERSITY", {
    x: 11.25, y: 0.77, w: 1.85, h: 0.12, fontFace: "Arial", fontSize: 3.9, color: "FFFFFF", margin: 0,
  });
  slide.addText(`EMPIRICAL RESULTS / ${String(num).padStart(2, "0")}`, {
    x: 0.58, y: 0.28, w: 3.3, h: 0.24, fontFace: "Arial", fontSize: 9.2, color: C.ink, margin: 0,
  });
  slide.addText(kicker, {
    x: 7.7, y: 0.28, w: 2.55, h: 0.26, align: "right", fontFace: "Microsoft YaHei", fontSize: 8, color: C.muted, margin: 0,
  });
  slide.addText(title, {
    x: 0.58, y: 0.56, w: 9.5, h: 0.42, fontFace: "Microsoft YaHei", fontSize: 18, bold: true, color: C.ink, margin: 0,
  });
  slide.addText(subtitle, {
    x: 0.58, y: 1.08, w: 9.6, h: 0.28, fontFace: "Microsoft YaHei", fontSize: 8.5, color: C.muted, margin: 0,
  });
}

function cell(text, opts = {}) {
  return {
    text,
    options: {
      fontFace: "Microsoft YaHei",
      fontSize: opts.fontSize ?? 6.6,
      bold: opts.bold ?? false,
      color: opts.color ?? C.ink,
      fill: opts.fill ? { color: opts.fill } : undefined,
      align: opts.align ?? "center",
      valign: "middle",
      margin: opts.margin ?? 0.02,
      breakLine: false,
    },
  };
}

function table(slide, rows, x, y, w, h, colW, opts = {}) {
  slide.addTable(rows, {
    x, y, w, h,
    colW,
    border: { type: "solid", color: C.border, pt: 0.45 },
    fontFace: "Microsoft YaHei",
    fontSize: opts.fontSize ?? 6.6,
    color: C.ink,
    margin: 0.02,
    valign: "middle",
    autoFit: false,
    fit: "shrink",
  });
}

function label(slide, text, x, y, w) {
  slide.addText(text, {
    x, y, w, h: 0.18, margin: 0,
    fontFace: "Microsoft YaHei", fontSize: 7.8, bold: true, color: C.redDark,
  });
}

function explain(slide, title, bullets, x, y, w, h) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.06,
    fill: { color: "FFFFFF", transparency: 0 },
    line: { color: "D3C7B8", pt: 0.6 },
  });
  slide.addText(title, {
    x: x + 0.16, y: y + 0.13, w: w - 0.32, h: 0.24, margin: 0,
    fontFace: "Microsoft YaHei", fontSize: 9.2, bold: true, color: C.redDark,
  });
  slide.addText(bullets.map(b => `• ${b}`).join("\n"), {
    x: x + 0.18, y: y + 0.48, w: w - 0.34, h: h - 0.58, margin: 0,
    fontFace: "Microsoft YaHei", fontSize: 8.1, color: C.ink,
    breakLine: false, fit: "shrink", valign: "top",
    paraSpaceAfterPt: 3,
    bullet: { type: "ul" },
  });
}

function foot(slide, text) {
  slide.addText(text, {
    x: 0.48, y: 7.12, w: 12.25, h: 0.18, margin: 0,
    fontFace: "Microsoft YaHei", fontSize: 6.5, color: C.muted,
  });
}

function addTitleForTable(slide, text, x, y, w) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.32, rectRadius: 0.06, fill: { color: C.redDark }, line: { color: C.redDark } });
  slide.addText(text, { x: x + 0.06, y: y + 0.04, w: w - 0.12, h: 0.15, margin: 0, fontFace: "Microsoft YaHei", fontSize: 7.2, bold: true, color: "FFFFFF" });
}

// Slide 1: Tables 2 and 3
{
  const s = pptx.addSlide();
  addHeader(s, 1, "约束性治理", "表二与表三：绿色信贷首先体现为强度压降和污染治理", "连续煤炭暴露度 DID；核心解释变量为 Post2012 × 政策前煤炭暴露度。");

  addTitleForTable(s, "表二：能源强度压降", 0.46, 1.42, 6.18);
  const t2 = [
    ["变量", "绿色TFP", "GML", "五类能源强度", "煤炭终端强度"].map((v,i)=>cell(v,{bold:true,fill:C.head,fontSize:i?6.2:6.6})),
    [cell("政策后×煤炭暴露",{bold:true,align:"left",fill:C.pale}), cell("-1.0498"), cell("-0.1342"), cell("-0.2895**"), cell("-0.4262***")],
    [cell("标准误",{align:"left"}), cell("(0.7528)"), cell("(0.0830)"), cell("(0.1190)"), cell("(0.0776)")],
    [cell("样本量",{align:"left"}), cell("510"), cell("510"), cell("480"), cell("480")],
    [cell("R²",{align:"left"}), cell("0.7644"), cell("0.2719"), cell("0.9592"), cell("0.9237")],
    [cell("省份/年份FE",{align:"left"}), cell("是"), cell("是"), cell("是"), cell("是")],
  ];
  table(s, t2, 0.46, 1.67, 6.18, 1.78, [1.25,1.12,0.9,1.4,1.5]);

  addTitleForTable(s, "表三：污染治理响应", 0.46, 3.72, 6.18);
  const t3 = [
    ["变量", "工业SO₂", "NOx", "颗粒物", "工业固废", "工业废水"].map((v,i)=>cell(v,{bold:true,fill:C.head,fontSize:i?6.0:6.6})),
    [cell("政策后×煤炭暴露",{bold:true,align:"left",fill:C.pale}), cell("-72.5887***"), cell("-43.9915**"), cell("-10.1339"), cell("-47.2683**"), cell("-40594.6149")],
    [cell("标准误",{align:"left"}), cell("(19.6996)"), cell("(16.8916)"), cell("(28.0627)"), cell("(20.0521)"), cell("(24203.0698)")],
    [cell("样本量",{align:"left"}), cell("510"), cell("336"), cell("154"), cell("510"), cell("510")],
    [cell("R²",{align:"left"}), cell("0.8812"), cell("0.9223"), cell("0.8225"), cell("0.7837"), cell("0.9108")],
    [cell("省份/年份FE",{align:"left"}), cell("是"), cell("是"), cell("是"), cell("是"), cell("是")],
  ];
  table(s, t3, 0.46, 3.97, 6.18, 1.9, [1.15,1.05,0.85,0.9,1.0,1.23]);

  explain(s, "结果解释", [
    "能源强度和煤炭终端强度显著下降，说明绿色信贷首先压低高煤炭体系内部的运行强度。",
    "绿色TFP和GML不显著，因此不能表述为生产率跃升。",
    "污染治理证据集中在工业SO₂、NOx和工业固废；颗粒物和废水不稳，不能说全面污染改善。",
  ], 7.02, 1.55, 5.45, 4.78);
  foot(s, "注：括号内为标准误；所有全国连续DID控制 GDP、人口、工业占比、城镇化率、环保财政支出占比、市场化指数，并控制省份与年份固定效应，标准误按省份聚类。");
}

// Slide 2: Table 4
{
  const s = pptx.addSlide();
  addHeader(s, 2, "结构边界", "表四：煤炭占比下降，但不等于结构性去煤完成", "同一连续煤炭暴露度 DID；检验煤炭消费比例、碳排放和火电结构是否同步变化。");
  addTitleForTable(s, "表四：从约束性治理到结构性治理", 0.58, 1.55, 11.9);
  const rows = [
    ["变量", "五类能源煤炭占比", "原口径煤炭占比", "CO₂排放对数", "火电装机占比", "火电发电占比"].map((v,i)=>cell(v,{bold:true,fill:C.head,fontSize:i?7.0:7.2})),
    [cell("政策后×煤炭暴露",{bold:true,align:"left",fill:C.pale}), cell("-0.2495***"), cell("-0.1900***"), cell("-0.0982"), cell("0.0517"), cell("0.0888")],
    [cell("标准误",{align:"left"}), cell("(0.0754)"), cell("(0.0651)"), cell("(0.1034)"), cell("(0.0945)"), cell("(0.0754)")],
    [cell("样本量",{align:"left"}), cell("480"), cell("480"), cell("510"), cell("510"), cell("507")],
    [cell("R²",{align:"left"}), cell("0.9224"), cell("0.9382"), cell("0.9904"), cell("0.9368"), cell("0.9478")],
    [cell("省份/年份FE",{align:"left"}), cell("是"), cell("是"), cell("是"), cell("是"), cell("是")],
  ];
  table(s, rows, 0.58, 1.84, 11.9, 2.15, [1.45,2.08,2.08,1.95,2.08,2.08], {fontSize:7.2});
  explain(s, "结果解释", [
    "两个煤炭占比变量均显著下降，说明约束效应已经外溢到能源使用比例。",
    "CO₂、火电装机占比和火电发电占比不显著，说明煤炭占比下降没有同步转化为火电资本和发电结构重组。",
    "因此煤炭占比下降只能定位为过渡性调整，不是结构性治理完成的证据。",
  ], 0.78, 4.35, 11.45, 1.75);
  foot(s, "注：表中结构变量使用连续煤炭暴露度DID；火电发电占比存在政策前趋势问题，在论文中作为结构锁定边界证据而非强因果证据。");
}

// Slide 3: Table 5
{
  const s = pptx.addSlide();
  addHeader(s, 3, "条件路径", "表五：低碳禀赋不是结构性治理的充分条件", "后期DDD模型检验高煤炭暴露地区能否借助早期低碳基础进一步形成新能源替代。");
  addTitleForTable(s, "表五：结构性治理条件的DDD检验", 0.58, 1.45, 11.9);
  const rows = [
    ["变量", "非火电发电占比", "风电发电占比", "风光发电占比", "风电装机占比"].map((v,i)=>cell(v,{bold:true,fill:C.head,fontSize:i?7.3:7.4})),
    [cell("后期×煤炭暴露",{bold:true,align:"left",fill:C.pale}), cell("-0.2231*"), cell("0.0024"), cell("-0.0919"), cell("0.0273")],
    [cell("标准误",{align:"left"}), cell("(0.1164)"), cell("(0.0240)"), cell("(0.0724)"), cell("(0.0675)")],
    [cell("后期×低碳禀赋",{bold:true,align:"left",fill:C.pale}), cell("0.1072"), cell("0.0309"), cell("0.0908*"), cell("0.0246")],
    [cell("标准误",{align:"left"}), cell("(0.0695)"), cell("(0.0182)"), cell("(0.0461)"), cell("(0.0329)")],
    [cell("三重交互项",{bold:true,align:"left",fill:C.pale}), cell("-0.1757"), cell("-0.0927**"), cell("-0.2363**"), cell("-0.1077")],
    [cell("标准误",{align:"left"}), cell("(0.1514)"), cell("(0.0402)"), cell("(0.1093)"), cell("(0.0821)")],
    [cell("样本量 / R²",{align:"left"}), cell("507 / 0.9514"), cell("330 / 0.8916"), cell("330 / 0.8921"), cell("288 / 0.9311")],
    [cell("省份/年份FE",{align:"left"}), cell("是"), cell("是"), cell("是"), cell("是")],
  ];
  table(s, rows, 0.58, 1.74, 11.9, 3.33, [1.75,2.55,2.55,2.55,2.5], {fontSize:7.2});
  explain(s, "结果解释", [
    "低碳禀赋本身对后期风光发电占比有一定正向关系，但三重交互项在风电和风光发电占比上显著为负。",
    "因此不能写成“低碳禀赋强化绿色信贷的新能源替代效应”。",
    "更稳的解释是：低碳禀赋只是前置条件，结构性治理还受项目建设、电网消纳、外送通道和政策连续性约束。",
  ], 0.78, 5.36, 11.45, 1.18);
  foot(s, "注：低碳禀赋 = 政策前非火电装机、早期风电装机、早期风电发电三个标准化变量的均值；省份层面的煤炭暴露×低碳禀赋被省份固定效应吸收。");
}

// Slide 4: Table 6
{
  const s = pptx.addSlide();
  addHeader(s, 4, "晋蒙路径", "表六：政策文本证据展示两类地方路径", "先看2012年后两省文本均值，再用回归系数识别内蒙古相对山西的政策后差异。");
  addTitleForTable(s, "表六A：2012年后晋蒙政策文本均值", 0.42, 1.42, 12.36);
  const rows = [
    ["省份", "绿金词频", "绿金覆盖", "煤炭清洁词频", "煤炭清洁覆盖", "污染词频", "污染覆盖", "新能源词频", "新能源覆盖"].map((v,i)=>cell(v,{bold:true,fill:C.head,fontSize:i?5.9:6.2})),
    [cell("山西",{bold:true,align:"left",fill:C.pale}), cell("0.3420"), cell("0.0880"), cell("7.6351"), cell("0.2193"), cell("2.2880"), cell("0.1459"), cell("2.6417"), cell("0.1346")],
    [cell("内蒙古",{bold:true,align:"left",fill:C.pale}), cell("0.6212"), cell("0.1083"), cell("3.3468"), cell("0.1530"), cell("1.6384"), cell("0.1030"), cell("4.3503"), cell("0.1276")],
  ];
  table(s, rows, 0.42, 1.7, 12.36, 1.18, [1.18,1.18,1.18,1.58,1.58,1.18,1.18,1.44,1.44], {fontSize:6.0});

  addTitleForTable(s, "表六B：内蒙古相对山西的政策后差异", 0.42, 3.16, 12.36);
  const diffRows = [
    ["变量", "绿金词频", "绿金覆盖", "煤炭清洁词频", "煤炭清洁覆盖", "污染词频", "污染覆盖", "新能源词频", "新能源覆盖"].map((v,i)=>cell(v,{bold:true,fill:C.head,fontSize:i?5.85:6.1})),
    [cell("内蒙古×2012后",{bold:true,align:"left",fill:C.pale,fontSize:5.8}), cell("0.3062*"), cell("0.0382**"), cell("9.3511***"), cell("0.1361***"), cell("0.1263"), cell("0.0299"), cell("1.2466"), cell("0.0102")],
    [cell("标准误",{align:"left"}), cell("(0.1577)"), cell("(0.0145)"), cell("(2.4313)"), cell("(0.0398)"), cell("(0.7338)"), cell("(0.0203)"), cell("(1.6355)"), cell("(0.0167)")],
  ];
  table(s, diffRows, 0.42, 3.44, 12.36, 1.15, [1.45,1.12,1.12,1.5,1.5,1.12,1.12,1.34,1.34], {fontSize:5.95});
  explain(s, "结果解释", [
    "均值显示，山西在煤炭清洁治理和污染治理议题上更集中，内蒙古在绿色金融和新能源词频上更突出。",
    "回归差异项反映内蒙古相对山西的政策后变化，说明政策文本中的路径差异，而不是两省绝对水平高低。",
    "汇报时可概括为：山西偏存量煤炭治理，内蒙古更容易围绕风光资源与清洁电力基础形成增量转型叙事。",
  ], 0.78, 5.0, 11.45, 1.28);
  foot(s, "注：词频为每万字关键词出现次数，覆盖比例为含对应关键词文件占比；回归项为两省样本、控制省份和年份固定效应的内蒙古相对山西政策后差异。");
}

async function main() {
  if (fs.existsSync(OUT) && !fs.existsSync(BACKUP)) {
    fs.copyFileSync(OUT, BACKUP);
  }
  await pptx.writeFile({ fileName: OUT });
  console.log(`Wrote ${OUT}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
