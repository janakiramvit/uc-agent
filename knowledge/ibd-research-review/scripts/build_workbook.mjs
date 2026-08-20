import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "/Users/janakirampulipati/ibd-research-review";
const data = JSON.parse(await fs.readFile(path.join(root, "processing/checkpoints/research-data.json"), "utf8"));
const summary = JSON.parse(await fs.readFile(path.join(root, "run-summary.json"), "utf8"));
const workbook = Workbook.create();

const palette = {
  navy: "#16324F", blue: "#2D6A8A", teal: "#3A7D78", pale: "#EAF3F4",
  cream: "#F7F3EA", amber: "#F4C95D", red: "#C94C4C", green: "#DCEFE3",
  gray: "#E5E7EB", white: "#FFFFFF", ink: "#1F2937",
};

function letters(n) {
  let s = "";
  while (n > 0) {
    n--;
    s = String.fromCharCode(65 + (n % 26)) + s;
    n = Math.floor(n / 26);
  }
  return s;
}

function value(v) {
  if (Array.isArray(v)) return v.join("; ");
  if (v === null || v === undefined) return "";
  if (typeof v === "object") return JSON.stringify(v);
  return v;
}

function addDataSheet(name, title, subtitle, columns, rows, options = {}) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  const lastCol = letters(columns.length);
  sheet.getRange(`A1:${lastCol}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A2:${lastCol}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A1:${lastCol}1`).format = {
    fill: palette.navy, font: { bold: true, color: palette.white, size: 16 },
    verticalAlignment: "center",
  };
  sheet.getRange(`A2:${lastCol}2`).format = {
    fill: palette.pale, font: { color: palette.ink, italic: true, size: 10 },
    wrapText: true, verticalAlignment: "center",
  };
  sheet.getRange("A1").format.rowHeight = 28;
  sheet.getRange("A2").format.rowHeight = 36;
  const headers = columns.map(c => c.header);
  sheet.getRange(`A4:${lastCol}4`).values = [headers];
  sheet.getRange(`A4:${lastCol}4`).format = {
    fill: palette.blue, font: { bold: true, color: palette.white, size: 10 },
    wrapText: true, verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: palette.navy },
  };
  sheet.getRange(`A4:${lastCol}4`).format.rowHeight = 34;
  const matrix = rows.map(row => columns.map(c => value(row[c.key])));
  if (matrix.length) {
    sheet.getRange(`A5:${lastCol}${4 + matrix.length}`).values = matrix;
    sheet.getRange(`A5:${lastCol}${4 + matrix.length}`).format = {
      font: { color: palette.ink, size: 9 },
      wrapText: true, verticalAlignment: "top",
      borders: { insideHorizontal: { style: "thin", color: "#D7DEE4" } },
    };
    sheet.getRange(`A5:${lastCol}${4 + matrix.length}`).format.rowHeight = options.rowHeight || 58;
    const table = sheet.tables.add(`A4:${lastCol}${4 + matrix.length}`, true, `${name.replace(/[^A-Za-z0-9]/g, "")}Table`);
    table.style = "TableStyleMedium2";
    table.showFilterButton = true;
    table.showBandedRows = true;
  }
  columns.forEach((c, idx) => {
    sheet.getRange(`${letters(idx + 1)}:${letters(idx + 1)}`).format.columnWidth = c.width || 16;
  });
  sheet.freezePanes.freezeRows(4);
  if (options.freezeColumns) sheet.freezePanes.freezeColumns(options.freezeColumns);
  return sheet;
}

const sourcesColumns = [
  ["sourceId","Source ID",12],["sourceTitle","Source title",38],["sourceType","Source type",14],
  ["authors","Authors or organisation",30],["publicationYear","Year",9],["countryOrRegion","Country or region",18],
  ["canonicalUrl","URL",34],["doi","DOI",20],["studyType","Study type",22],
  ["conditionApplicability","Condition applicability",23],["diseaseContext","Disease context",24],
  ["population","Population",30],["sampleSize","Sample size",16],["mainRelevantFinding","Main relevant finding",42],
  ["outcomes","Outcomes",25],["limitations","Limitations",38],["applicabilityLimitations","Applicability limitations",38],
  ["regionalApplicability","Regional applicability",38],["relevantTopics","Relevant topics",25],
  ["fullTextAvailability","Full-text availability",18],["sourceQuality","Source quality",14],
  ["directRelevance","Direct relevance",14],["addedValue","Added value",28],["recommendation","Recommendation",16],
  ["recommendationReason","Recommendation reason",34],["userDecision","User decision",18],["userNotes","User notes",30],
].map(([key,header,width]) => ({key,header,width}));

const sourceRows = data.sources.map(s => ({
  ...s, authors: s.authors || s.issuingOrganisation, userDecision: "", userNotes: "",
}));
const sourcesSheet = addDataSheet("Sources", "Selected evidence sources",
  "All sources remain pending human review. Blank yellow columns are reviewer inputs; evidence quality is not approval.",
  sourcesColumns, sourceRows, {freezeColumns: 2, rowHeight: 72});
sourcesSheet.getRange(`Z5:AA${4 + sourceRows.length}`).format.fill = "#FFF4CC";
sourcesSheet.getRange(`Z5:Z${4 + sourceRows.length}`).dataValidation = {
  rule: { type: "list", values: ["Approve", "Reject", "Needs more evidence"] },
};

const claimsColumns = [
  ["claimId","Claim ID",12],["sourceId","Source ID",12],["sourceTitle","Source title",34],["sourceType","Source type",14],
  ["conditionApplicability","Condition applicability",22],["diseaseContext","Disease context",23],["topic","Topic",22],
  ["outcomeType","Outcome type",20],["claim","Candidate claim",44],["plainLanguageExplanation","Plain-language explanation",44],
  ["possibleProductUse","Possible product use",34],["supportingExcerpt","Supporting excerpt",46],["pageNumber","Page number",12],
  ["sectionHeading","Section heading",18],["evidenceLevel","Evidence level",20],["studyType","Study type",22],
  ["population","Population",28],["countryOrRegion","Country or region",18],["limitations","Limitations",38],
  ["applicabilityLimitations","Applicability limitations",38],["regionalApplicability","Regional applicability",38],
  ["confidence","Confidence",12],["userDecision","User decision",18],["userEditedClaim","User-edited claim",42],
  ["reviewerNotes","Reviewer notes",34],
].map(([key,header,width]) => ({key,header,width}));
const claimsSheet = addDataSheet("Claims", "Retained candidate claims",
  "Every claim is traceable to a passage and remains pending human review. Symptom outcomes are not treated as proof of reduced inflammation.",
  claimsColumns, data.claims, {freezeColumns: 2, rowHeight: 84});
claimsSheet.getRange(`W5:Y${4 + data.claims.length}`).format.fill = "#FFF4CC";
claimsSheet.getRange(`W5:W${4 + data.claims.length}`).dataValidation = {
  rule: { type: "list", values: ["Approve", "Reject", "Edit", "Needs more evidence"] },
};

const coverageSheet = addDataSheet("Coverage Matrix", "Evidence coverage matrix",
  "Counts reflect retained candidate claims, not approved claims. Under-covered means fewer than three candidate claims in this bounded run.",
  [
    {key:"category",header:"Coverage category",width:22},{key:"dimension",header:"Dimension",width:34},
    {key:"claimCount",header:"Candidate claims",width:16},{key:"coverageStatus",header:"Coverage status",width:18},
    {key:"reviewNote",header:"Interpretation",width:48},
  ], data.coverage, {rowHeight: 42});
coverageSheet.getRange(`D5:D${4 + data.coverage.length}`).conditionalFormats.add("containsText", {
  text: "Under-covered", format: { fill: "#FDE2E2", font: { bold: true, color: "#8A1C1C" } },
});
coverageSheet.getRange(`C5:C${4 + data.coverage.length}`).conditionalFormats.add("dataBar", {
  color: palette.teal, gradient: true,
});

const duplicateRows = data.duplicates.length ? data.duplicates : [{
  groupId: "None detected", recordType: "", recordA: "", recordB: "",
  similarity: "", reason: "No duplicate or near-duplicate groups met the configured similarity threshold.",
}];
addDataSheet("Duplicates", "Duplicate and near-duplicate review",
  "Potential duplicates are preserved rather than silently merged.",
  [
    {key:"groupId",header:"Group ID",width:14},{key:"recordType",header:"Record type",width:16},
    {key:"recordA",header:"Record A",width:16},{key:"recordB",header:"Record B",width:16},
    {key:"similarity",header:"Similarity",width:12},{key:"reason",header:"Reason for flag",width:50},
  ], duplicateRows, {rowHeight: 40});

addDataSheet("Conflicts", "Conflict and non-comparability review",
  "Flags identify differences that require human interpretation; they do not assert that either claim is wrong.",
  [
    {key:"conflictId",header:"Conflict ID",width:14},{key:"claimA",header:"Claim A",width:14},
    {key:"claimB",header:"Claim B",width:14},{key:"topic",header:"Topic",width:22},
    {key:"conditionDifference",header:"Condition differences",width:18},
    {key:"diseaseStateDifference",header:"Disease-state differences",width:20},
    {key:"populationDifference",header:"Population differences",width:24},
    {key:"evidenceLevelDifference",header:"Evidence-level differences",width:20},
    {key:"symptomVsInflammation",header:"Symptoms vs inflammation",width:20},
    {key:"regionalDifference",header:"Regional differences",width:26},
    {key:"reason",header:"Reason for conflict flag",width:42},
  ], data.conflicts, {rowHeight: 48});

addDataSheet("Acquisition Failures", "Acquisition failures and fallbacks",
  "Only open, legally accessible acquisition was attempted. Paywalls were not bypassed.",
  [
    {key:"source",header:"Source",width:38},{key:"sourceType",header:"Source type",width:16},
    {key:"attemptedMethod",header:"Attempted method",width:20},{key:"failureStatus",header:"Failure status",width:18},
    {key:"failureReason",header:"Failure reason",width:48},{key:"retryCount",header:"Retry count",width:12},
    {key:"abstractOnlyUsed",header:"Abstract-only evidence used",width:22},
  ], data.acquisitionFailures, {rowHeight: 50});

addDataSheet("Rejected Candidates", "Rejected and deferred source candidates",
  "Rejection reflects this bounded first-pass selection, not necessarily scientific invalidity.",
  [
    {key:"source",header:"Candidate source",width:48},{key:"reason",header:"Decision reason",width:54},
  ], data.rejectedCandidates, {rowHeight: 44});

const summaryRows = [
  ["Searches performed", summary.searchesPerformed, "Bounded structured PubMed/authority searches"],
  ["Candidates found", summary.candidatesFound, "Deduplicated candidates within configured cap"],
  ["Sources selected", summary.sourcesSelected, "All pending human review"],
  ["Source-type breakdown", JSON.stringify(summary.sourceTypeBreakdown), "Guidelines, reviews, studies, and official explanations"],
  ["Ulcerative-colitis-specific sources", summary.ulcerativeColitisSpecificSources, ""],
  ["Crohn’s-specific sources", summary.crohnsSpecificSources, ""],
  ["Shared IBD sources", summary.sharedIBDSources, ""],
  ["Full-text acquisitions", summary.fullTextAcquisitions, "Open public full text only"],
  ["Abstract-only acquisitions", summary.abstractOnlyAcquisitions, "Labelled and limited in confidence"],
  ["Chunks generated", summary.chunksGenerated, "Sentence-safe bounded chunks"],
  ["Claims retained", summary.claimsRetained, "Pending human review"],
  ["Claims rejected", summary.claimsRejected, "Safety, traceability, or cap reasons"],
  ["Duplicates", summary.duplicates, "Potential near-duplicates preserved"],
  ["Conflicts", summary.conflicts, "Non-comparability/conflict flags preserved"],
  ["Coverage gaps", summary.coverageGaps.join("; "), "Under three candidate claims"],
  ["Regional-applicability gaps", summary.regionalApplicabilityGaps, "Dimensions needing deeper Canada/US review"],
  ["Limits reached", summary.limitsReached.join("; ") || "None", "No limit silently exceeded"],
  ["API usage", JSON.stringify(summary.estimatedApiUsage), "Paid model calls: 0"],
  ["Errors", summary.errors.length, "See Acquisition Failures"],
  ["Execution date", `Run time: ${summary.executionDate}`, "UTC"],
  ["Review status", summary.reviewStatus, "Hard stop pending human approval"],
].map(([metric,value,note]) => ({metric,value,note}));
const runSheet = addDataSheet("Run Summary", "Research-review run summary",
  "This package is complete for review but contains no approvals and must not be copied into an application before explicit human approval.",
  [
    {key:"metric",header:"Metric",width:34},{key:"value",header:"Value",width:46},{key:"note",header:"Interpretation",width:52},
  ], summaryRows, {rowHeight: 42});
runSheet.getRange(`A5:A${4 + summaryRows.length}`).format.font = { bold: true, color: palette.navy };
runSheet.getRange(`B5:B${4 + summaryRows.length}`).format.fill = palette.cream;

const previewDir = path.join(root, "previews");
await fs.mkdir(previewDir, { recursive: true });
const sheetNames = ["Sources","Claims","Coverage Matrix","Duplicates","Conflicts","Acquisition Failures","Rejected Candidates","Run Summary"];
const verification = { sheets: [], formulaErrors: null };
for (const sheetName of sheetNames) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 0.8, format: "png" });
  const outPath = path.join(previewDir, `${sheetName.replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()}.png`);
  await fs.writeFile(outPath, new Uint8Array(await preview.arrayBuffer()));
  verification.sheets.push({ sheetName, preview: outPath });
}
const errors = await workbook.inspect({
  kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan",
});
verification.formulaErrors = errors.ndjson;
const keyRanges = {};
for (const [sheetName, range] of Object.entries({
  "Sources": "A1:AA9", "Claims": "A1:Y9", "Coverage Matrix": "A1:E20",
  "Run Summary": "A1:C25",
})) {
  const check = await workbook.inspect({ kind: "table", range: `${sheetName}!${range}`, include: "values,formulas", tableMaxRows: 25, tableMaxCols: 27 });
  keyRanges[sheetName] = check.ndjson;
}
verification.keyRanges = keyRanges;
await fs.writeFile(path.join(root, "logs/workbook-verification.json"), JSON.stringify(verification, null, 2));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(root, "ibd-evidence-review.xlsx"));
console.log(JSON.stringify({ workbook: path.join(root, "ibd-evidence-review.xlsx"), previews: verification.sheets.length }));
