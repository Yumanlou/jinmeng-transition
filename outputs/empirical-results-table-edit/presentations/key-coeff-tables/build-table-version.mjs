import fs from "node:fs/promises";
import path from "node:path";
import { ensureArtifactToolWorkspace, importArtifactTool, saveBlobToFile } from "/Users/yumanlou/.codex/plugins/cache/openai-primary-runtime/presentations/26.521.10419/skills/presentations/scripts/artifact_tool_utils.mjs";

const workspace = path.resolve("/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型/outputs/empirical-results-table-edit/presentations/key-coeff-tables");
const sourcePptx = path.resolve("/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型/output/实证结果汇报_四页.pptx");
const finalPptx = path.resolve("/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型/output/实证结果汇报_四页_表格版.pptx");
const previewDir = path.join(workspace, "preview", "final");
const layoutDir = path.join(workspace, "layout", "final");

const navy = "#092565";
const body = "#1E293B";

const tables = [
  {
    values: [
      ["结果变量", "核心系数", "标准误"],
      ["五类能源强度", "-0.2895**", "(0.1190)"],
      ["煤炭终端强度", "-0.4262***", "(0.0776)"],
      ["绿色全要素生产率", "-1.0498", "(0.7528)"],
      ["全局ML指数", "-0.1342", "(0.0830)"],
    ],
    significantRows: [1, 2],
    note: "注：括号内为标准误；控制省份和年份固定效应。",
  },
  {
    values: [
      ["结果变量", "核心系数", "标准误"],
      ["工业二氧化硫", "-72.5887***", "(19.6996)"],
      ["氮氧化物", "-43.9915**", "(16.8916)"],
      ["工业固废", "-47.2683**", "(20.0521)"],
      ["颗粒物", "-10.1339", "(28.0627)"],
      ["工业废水", "-40594.6149", "(24203.0698)"],
    ],
    significantRows: [1, 2, 3],
    note: "注：括号内为标准误；控制省份和年份固定效应。",
  },
  {
    values: [
      ["结果变量", "核心系数", "标准误"],
      ["煤炭占比（五类）", "-0.2495***", "(0.0754)"],
      ["煤炭占比（原口径）", "-0.1900***", "(0.0651)"],
      ["二氧化碳（对数）", "-0.0982", "(0.1034)"],
      ["火电装机占比", "0.0517", "(0.0945)"],
      ["火电发电占比", "0.0888", "(0.0754)"],
    ],
    significantRows: [1, 2],
    note: "注：括号内为标准误；控制省份和年份固定效应。",
  },
];

function stylizeTable(table, significantRows = []) {
  for (let row = 0; row < table.rowCount; row += 1) {
    for (let col = 0; col < table.columnCount; col += 1) {
      const style = table.getCell(row, col).textStyle;
      style.typeface = "微软雅黑";
      style.fontSize = row === 0 ? 11 : 10.5;
      style.color = row === 0 ? navy : body;
      style.bold = row === 0 || significantRows.includes(row);
    }
  }
}

function addMainTable(slide, spec) {
  const note = slide.shapes.getById("23");
  note.text = spec.note;
  note.frame = { left: 105, top: 426, width: 345, height: 28 };
  note.text.fontSize = 9.5;
  note.text.color = "#536273";
  note.text.typeface = "微软雅黑";

  const table = slide.tables.add({
    rows: spec.values.length,
    columns: 3,
    values: spec.values,
    columnWidths: [154, 108, 83],
  });
  table.frame = {
    left: 105,
    top: 216,
    width: 345,
    height: spec.values.length === 5 ? 174 : 198,
  };
  stylizeTable(table, spec.significantRows);
}

function addConditionalTables(slide) {
  const note = slide.shapes.getById("23");
  note.text = "注：三重差分包含低阶交互项；政策文本仅刻画后验政策注意力。";
  note.frame = { left: 105, top: 453, width: 345, height: 27 };
  note.text.fontSize = 9;
  note.text.color = "#536273";
  note.text.typeface = "微软雅黑";

  const ddd = [
    ["低碳禀赋检验", "风电发电", "风光发电"],
    ["后期低碳禀赋", "0.0309", "0.0908*"],
    ["三重交互", "-0.0927**", "-0.2363**"],
  ];
  const table1 = slide.tables.add({
    rows: ddd.length,
    columns: 3,
    values: ddd,
    columnWidths: [146, 100, 99],
  });
  table1.frame = { left: 105, top: 205, width: 345, height: 102 };
  stylizeTable(table1, [2]);

  const text = [
    ["晋蒙政策文本", "词频", "覆盖比例"],
    ["绿色金融", "0.3062*", "0.0382**"],
    ["煤炭清洁治理", "9.3511***", "0.1361***"],
  ];
  const table2 = slide.tables.add({
    rows: text.length,
    columns: 3,
    values: text,
    columnWidths: [146, 100, 99],
  });
  table2.frame = { left: 105, top: 333, width: 345, height: 102 };
  stylizeTable(table2, [1, 2]);
}

await ensureArtifactToolWorkspace(workspace);
const { FileBlob, PresentationFile } = await importArtifactTool(workspace);
const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePptx));
for (let index = 0; index < 3; index += 1) addMainTable(presentation.slides.getItem(index), tables[index]);
addConditionalTables(presentation.slides.getItem(3));

await fs.mkdir(path.dirname(finalPptx), { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(layoutDir, { recursive: true });
for (let index = 0; index < presentation.slides.count; index += 1) {
  const slide = presentation.slides.getItem(index);
  const suffix = String(index + 1).padStart(2, "0");
  await saveBlobToFile(await presentation.export({ slide, format: "png", scale: 1 }), path.join(previewDir, `slide-${suffix}.png`));
  await saveBlobToFile(await presentation.export({ slide, format: "layout" }), path.join(layoutDir, `slide-${suffix}.layout.json`));
}
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(finalPptx);
console.log(finalPptx);
process.exit(0);
