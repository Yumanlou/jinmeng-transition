import path from "node:path";
import { ensureArtifactToolWorkspace, importArtifactTool } from "/Users/yumanlou/.codex/plugins/cache/openai-primary-runtime/presentations/26.521.10419/skills/presentations/scripts/artifact_tool_utils.mjs";

const workspace = path.resolve("/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型/outputs/empirical-results-table-edit/presentations/key-coeff-tables");
const pptxPath = path.resolve("/Users/yumanlou/Library/CloudStorage/OneDrive-email.cufe.edu.cn/2026/寒假/晋蒙转型/output/实证结果汇报_四页.pptx");
await ensureArtifactToolWorkspace(workspace);
const { FileBlob, PresentationFile, PresentationTable } = await importArtifactTool(workspace);
const presentation = await PresentationFile.importPptx(await FileBlob.load(pptxPath));
const slide = presentation.slides.getItem(0);
console.log("tables prototype", Object.getOwnPropertyNames(Object.getPrototypeOf(slide.tables)));
console.log("table class", PresentationTable && Object.getOwnPropertyNames(PresentationTable.prototype));
console.log("tables add fn", slide.tables.add.toString().slice(0, 600));
console.log("table ctor", PresentationTable?.toString().slice(0, 300));
const content = slide.shapes.getById("23");
console.log("shape23 position proto", Object.getOwnPropertyNames(Object.getPrototypeOf(content.position)));
console.log("shape23 pixelRect", content.pixelRect, "position snapshot", content.position?.toProto?.(), "shape snapshot", content.toSnapshot?.());
const tab = slide.tables.add({
  position: { left: 105, top: 210, width: 345, height: 100 },
  rows: 2,
  columns: 2,
  values: [["指标", "估计值"], ["A", "1.0"]],
  columnWidths: [190, 155],
});
console.log("table proto", Object.getOwnPropertyNames(Object.getPrototypeOf(tab)), tab.toSnapshot?.());
const cell = tab.getCell(0, 0);
console.log("cell proto", Object.getOwnPropertyNames(Object.getPrototypeOf(cell)), cell.toSnapshot?.(), Object.keys(cell));
process.exit(0);
