import path from "node:path";
import fs from "node:fs/promises";
import { ensureArtifactToolWorkspace, importArtifactTool, saveBlobToFile } from "/Users/yumanlou/.codex/plugins/cache/openai-primary-runtime/presentations/26.521.10419/skills/presentations/scripts/artifact_tool_utils.mjs";

const workspace = path.resolve("/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型/outputs/empirical-results-table-edit/presentations/key-coeff-tables");
const source = path.resolve("/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型/output/实证结果汇报_四页.pptx");
await ensureArtifactToolWorkspace(workspace);
const { FileBlob, PresentationFile } = await importArtifactTool(workspace);
const presentation = await PresentationFile.importPptx(await FileBlob.load(source));
const slide = presentation.slides.getItem(0);
const note = slide.shapes.getById("23");
note.text = "注：括号内为标准误；省份和年份固定效应均已控制。";
note.frame = { left: 105, top: 420, width: 345, height: 34 };
const values = [
  ["结果变量", "核心系数", "标准误"],
  ["五类能源强度", "-0.2895**", "(0.1190)"],
  ["煤炭终端强度", "-0.4262***", "(0.0776)"],
  ["绿色全要素生产率", "-1.0498", "(0.7528)"],
  ["全局ML指数", "-0.1342", "(0.0830)"],
  ["省份/年份固定效应", "是", "是"],
];
const table = slide.tables.add({ rows: values.length - 1, columns: 3, values: values.slice(0, -1), columnWidths: [160, 105, 80] });
table.frame = { left: 105, top: 220, width: 345, height: 168 };
for (let row = 0; row < table.rowCount; row += 1) {
  for (let col = 0; col < table.columnCount; col += 1) {
    const style = table.getCell(row, col).textStyle;
    style.fontSize = row === 0 ? 10 : 9.5;
    style.typeface = "微软雅黑";
    style.bold = row === 0;
  }
}
console.log("frame", table.toSnapshot());
await fs.mkdir(path.join(workspace, "test"), { recursive: true });
await saveBlobToFile(await presentation.export({ slide, format: "png", scale: 1 }), path.join(workspace, "test", "native-table-test.png"));
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(path.join(workspace, "test", "native-table-test.pptx"));
process.exit(0);
