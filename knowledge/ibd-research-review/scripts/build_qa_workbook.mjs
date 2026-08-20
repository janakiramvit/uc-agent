import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "/Users/janakirampulipati/ibd-research-review";
const qa = JSON.parse(await fs.readFile(path.join(root, "processing/checkpoints/qa-review.json"), "utf8"));
const workbook = Workbook.create();

const palette = {
  navy: "#17324D",
  blue: "#2E6882",
  teal: "#2E7D73",
  pale: "#EAF3F4",
  cream: "#F7F3EA",
  yellow: "#FFF2B2",
  red: "#F8D7DA",
  amber: "#FCE5B3",
  green: "#DDEFE2",
  gray: "#E5E7EB",
  white: "#FFFFFF",
  ink: "#1F2937",
};

function letters(n) {
  let s = "";
  while (n > 0) {
    n -= 1;
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

function column(key, header, width = 18) {
  return { key, header, width };
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
    fill: palette.navy,
    font: { bold: true, color: palette.white, size: 16 },
    verticalAlignment: "center",
  };
  sheet.getRange(`A2:${lastCol}2`).format = {
    fill: palette.pale,
    font: { color: palette.ink, italic: true, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange("A1").format.rowHeight = 30;
  sheet.getRange("A2").format.rowHeight = 42;
  sheet.getRange(`A4:${lastCol}4`).values = [columns.map((c) => c.header)];
  sheet.getRange(`A4:${lastCol}4`).format = {
    fill: palette.blue,
    font: { bold: true, color: palette.white, size: 10 },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: palette.navy },
  };
  sheet.getRange(`A4:${lastCol}4`).format.rowHeight = 38;
  if (rows.length) {
    const matrix = rows.map((row) => columns.map((c) => value(row[c.key])));
    const endRow = 4 + rows.length;
    sheet.getRange(`A5:${lastCol}${endRow}`).values = matrix;
    sheet.getRange(`A5:${lastCol}${endRow}`).format = {
      font: { color: palette.ink, size: 9 },
      wrapText: true,
      verticalAlignment: "top",
      borders: { insideHorizontal: { style: "thin", color: "#D6DEE5" } },
    };
    sheet.getRange(`A5:${lastCol}${endRow}`).format.rowHeight = options.rowHeight || 62;
    const table = sheet.tables.add(`A4:${lastCol}${endRow}`, true, `${name.replace(/[^A-Za-z0-9]/g, "")}Table`);
    table.style = "TableStyleMedium2";
    table.showFilterButton = true;
    table.showBandedRows = true;
  }
  columns.forEach((c, idx) => {
    sheet.getRange(`${letters(idx + 1)}:${letters(idx + 1)}`).format.columnWidth = c.width;
  });
  sheet.freezePanes.freezeRows(4);
  if (options.freezeColumns) sheet.freezePanes.freezeColumns(options.freezeColumns);
  return { sheet, columns, endRow: 4 + rows.length };
}

function findCol(columns, key) {
  return letters(columns.findIndex((c) => c.key === key) + 1);
}

function styleStatusColumn(sheet, col, endRow) {
  const range = sheet.getRange(`${col}5:${col}${endRow}`);
  range.conditionalFormats.add("containsText", {
    text: "ready_for_review",
    format: { fill: palette.green, font: { bold: true, color: "#155724" } },
  });
  range.conditionalFormats.add("containsText", {
    text: "revision",
    format: { fill: palette.amber, font: { bold: true, color: "#7A4A00" } },
  });
  range.conditionalFormats.add("containsText", {
    text: "needs",
    format: { fill: palette.amber, font: { bold: true, color: "#7A4A00" } },
  });
  range.conditionalFormats.add("containsText", {
    text: "insufficient",
    format: { fill: palette.amber, font: { bold: true, color: "#7A4A00" } },
  });
  range.conditionalFormats.add("containsText", {
    text: "superseded",
    format: { fill: palette.red, font: { bold: true, color: "#842029" } },
  });
  range.conditionalFormats.add("containsText", {
    text: "reject",
    format: { fill: palette.red, font: { bold: true, color: "#842029" } },
  });
}

const sourcesColumns = [
  column("sourceId", "Source ID", 12),
  column("sourceTitle", "Source title", 40),
  column("sourceType", "Source type", 15),
  column("authors", "Authors", 36),
  column("issuingOrganisation", "Issuing organisation", 24),
  column("journal", "Journal", 24),
  column("publicationYear", "Publication year", 12),
  column("sourceUrl", "Source URL", 34),
  column("canonicalUrl", "Canonical URL", 34),
  column("doi", "Original DOI", 24),
  column("pmid", "PMID", 12),
  column("pmcid", "Original PMCID", 16),
  column("studyType", "Study type", 22),
  column("conditionApplicability", "Condition applicability", 24),
  column("diseaseContext", "Disease context", 24),
  column("population", "Population", 30),
  column("sampleSize", "Sample size", 18),
  column("countryOrRegion", "Country or region", 18),
  column("interventionOrExposure", "Intervention or exposure", 32),
  column("comparator", "Comparator", 30),
  column("outcomes", "Outcomes", 28),
  column("mainRelevantFinding", "Main relevant finding", 44),
  column("limitations", "Limitations", 40),
  column("applicabilityLimitations", "Applicability limitations", 40),
  column("regionalApplicability", "Regional applicability", 40),
  column("relevantTopics", "Relevant topics", 26),
  column("fullTextAvailability", "Original full-text status", 20),
  column("acquisitionMethod", "Acquisition method", 22),
  column("acquisitionStatus", "Acquisition status", 18),
  column("sourceQuality", "Source quality", 14),
  column("directRelevance", "Direct relevance", 14),
  column("recommendation", "Original recommendation", 18),
  column("recommendationReason", "Original recommendation reason", 36),
  column("addedValue", "Added value", 30),
  column("qaStatus", "QA status", 24),
  column("verificationIssue", "Verification issue", 54),
  column("supersededStatus", "Superseded status", 28),
  column("verifiedDoi", "Verified DOI", 24),
  column("verifiedPmcid", "Verified PMCID", 18),
  column("verifiedFullTextStatus", "Verified access status", 30),
  column("alternativeAccessUrl", "Authoritative access URL", 38),
  column("supportingPassagesTraceable", "Supporting passages traceable", 26),
  column("recommendedReviewerAction", "Recommended reviewer action", 44),
  column("userDecision", "User decision", 22),
  column("userNotes", "User notes", 36),
];

const sourcesResult = addDataSheet(
  "Sources",
  "IBD evidence sources — QA review",
  "No source is approved. Original metadata is preserved; corrected metadata and verification issues are shown beside it. Yellow columns are blank human inputs.",
  sourcesColumns,
  qa.sources,
  { freezeColumns: 2, rowHeight: 84 },
);
const sourceQaCol = findCol(sourcesColumns, "qaStatus");
const sourceDecisionCol = findCol(sourcesColumns, "userDecision");
const sourceNotesCol = findCol(sourcesColumns, "userNotes");
styleStatusColumn(sourcesResult.sheet, sourceQaCol, sourcesResult.endRow);
sourcesResult.sheet.getRange(`${sourceDecisionCol}5:${sourceNotesCol}${sourcesResult.endRow}`).format.fill = palette.yellow;
sourcesResult.sheet.getRange(`${sourceDecisionCol}5:${sourceDecisionCol}${sourcesResult.endRow}`).dataValidation = {
  rule: { type: "list", values: ["Approve", "Reject", "Needs more evidence"] },
};

const claimsColumns = [
  column("claimId", "Claim ID", 12),
  column("sourceId", "Source ID", 12),
  column("sourceTitle", "Source title", 38),
  column("sourceType", "Source type", 14),
  column("sourceUrl", "Source URL", 34),
  column("conditionApplicability", "Condition applicability", 24),
  column("diseaseContext", "Disease context", 24),
  column("topic", "Topic", 22),
  column("outcomeType", "Outcome type", 20),
  column("claim", "Original candidate claim", 48),
  column("plainLanguageExplanation", "Original plain-language explanation", 48),
  column("possibleProductUse", "Possible product use", 38),
  column("supportingExcerpt", "Supporting excerpt", 50),
  column("sectionHeading", "Section heading", 20),
  column("pageNumber", "Page number", 12),
  column("evidenceLevel", "Evidence level", 20),
  column("studyType", "Study type", 22),
  column("population", "Population", 30),
  column("sampleSize", "Sample size", 18),
  column("countryOrRegion", "Country or region", 20),
  column("interventionOrExposure", "Intervention or exposure", 32),
  column("comparator", "Comparator", 30),
  column("outcome", "Outcome", 28),
  column("limitations", "Limitations", 40),
  column("applicabilityLimitations", "Applicability limitations", 40),
  column("regionalApplicability", "Regional applicability", 40),
  column("confidence", "Original confidence", 16),
  column("extractionMethod", "Extraction method", 24),
  column("reviewStatus", "Original review status", 22),
  column("qaStatus", "QA status", 28),
  column("originalClaim", "Original claim preserved", 48),
  column("proposedRevisedClaim", "Proposed revised claim", 54),
  column("revisionReason", "Revision reason", 48),
  column("verificationStatus", "Verification status", 34),
  column("conflictClassification", "Conflict classification", 28),
  column("recommendedReviewerAction", "Recommended reviewer action", 46),
  column("userDecision", "User decision", 26),
  column("userEditedClaim", "User-edited claim", 48),
  column("reviewerNotes", "Reviewer notes", 38),
];

const claimsResult = addDataSheet(
  "Claims",
  "IBD candidate claims — claim-level QA",
  "Original claims are preserved. Proposed wording is not approved wording. Yellow columns are blank human inputs; symptom, biomarker, and inflammation findings must remain distinct.",
  claimsColumns,
  qa.claims,
  { freezeColumns: 2, rowHeight: 96 },
);
const claimQaCol = findCol(claimsColumns, "qaStatus");
const claimDecisionCol = findCol(claimsColumns, "userDecision");
const claimNotesCol = findCol(claimsColumns, "reviewerNotes");
styleStatusColumn(claimsResult.sheet, claimQaCol, claimsResult.endRow);
claimsResult.sheet.getRange(`${claimDecisionCol}5:${claimNotesCol}${claimsResult.endRow}`).format.fill = palette.yellow;
claimsResult.sheet.getRange(`${claimDecisionCol}5:${claimDecisionCol}${claimsResult.endRow}`).dataValidation = {
  rule: { type: "list", values: ["Approve", "Reject", "Approve revised wording", "Needs more evidence"] },
};

const conflictColumns = [
  column("conflictId", "Flag ID", 14),
  column("claimIds", "Claim IDs", 22),
  column("sourceIds", "Source IDs", 20),
  column("topic", "Topic", 22),
  column("primaryClassification", "Primary classification", 28),
  column("secondaryClassifications", "Secondary classifications", 34),
  column("qaRationale", "Concise rationale", 54),
  column("bothClaimsMayCoexist", "Both claims may coexist", 20),
  column("sourcePriority", "Source priority", 32),
  column("wordingShouldBeNarrowed", "Narrow wording", 18),
  column("recommendedHumanAction", "Recommended human action", 48),
  column("conditionDifference", "Original condition difference", 20),
  column("diseaseStateDifference", "Original disease-state difference", 22),
  column("populationDifference", "Original population difference", 24),
  column("evidenceLevelDifference", "Original evidence-level difference", 22),
  column("symptomVsInflammation", "Original symptom vs inflammation", 22),
  column("regionalDifference", "Original regional difference", 26),
  column("reason", "Original flag reason", 38),
];
const conflictResult = addDataSheet(
  "Conflict Review",
  "Conflict and non-comparability QA",
  "All 80 original flags are preserved and classified exactly once. No winner is forced when records are not materially comparable.",
  conflictColumns,
  qa.conflicts,
  { freezeColumns: 3, rowHeight: 72 },
);
styleStatusColumn(conflictResult.sheet, findCol(conflictColumns, "primaryClassification"), conflictResult.endRow);

const coverageColumns = [
  column("dimension", "Coverage dimension", 30),
  column("candidateClaims", "Original candidate claims", 18),
  column("potentiallyUsableAfterQA", "Potentially usable after QA", 22),
  column("gapClassification", "Gap classification", 26),
  column("reviewNote", "Interpretation and scope limit", 56),
];
const coverageResult = addDataSheet(
  "Coverage Matrix",
  "Coverage after evidence QA",
  "Potentially usable means ready-for-review plus revision-recommended; it does not mean approved. Feature blocks apply only to the named scope.",
  coverageColumns,
  qa.coverage,
  { rowHeight: 56 },
);
styleStatusColumn(coverageResult.sheet, findCol(coverageColumns, "gapClassification"), coverageResult.endRow);
coverageResult.sheet.getRange(`C5:C${coverageResult.endRow}`).conditionalFormats.add("dataBar", {
  color: palette.teal,
  gradient: true,
});

const abstractColumns = [
  column("sourceId", "Source ID", 12),
  column("sourceTitle", "Source title", 42),
  column("originalStatus", "Original status", 18),
  column("verificationRoutes", "Legal/public verification routes", 44),
  column("fullTextBecameAvailable", "Full text became available", 22),
  column("currentAccessStatus", "Current access status", 32),
  column("accessUrl", "Authoritative access URL", 40),
  column("confidenceHandling", "Confidence handling", 42),
  column("applicabilityLimitation", "Applicability/access limitation", 48),
  column("recommendedAction", "Recommended reviewer action", 46),
];
const abstractResult = addDataSheet(
  "Abstract-Only Review",
  "Second-pass review of nine abstract-only sources",
  "Only legal public routes were used. Sources without full text remain explicitly abstract-only and must not be over-interpreted.",
  abstractColumns,
  qa.abstractOnlyReview,
  { freezeColumns: 2, rowHeight: 78 },
);
abstractResult.sheet.getRange(`E5:E${abstractResult.endRow}`).conditionalFormats.add("containsText", {
  text: "No",
  format: { fill: palette.amber, font: { bold: true, color: "#7A4A00" } },
});

const accessColumns = [
  column("issueId", "Issue ID", 12),
  column("sourceId", "Source ID", 12),
  column("issueType", "Issue type", 30),
  column("originalIssue", "Original issue", 54),
  column("verificationRoute", "Verification route", 48),
  column("resolutionStatus", "Resolution status", 30),
  column("authoritativeUrl", "Authoritative URL", 40),
  column("recommendedAction", "Recommended action", 48),
];
const accessResult = addDataSheet(
  "Access and Verification Issues",
  "Access, acquisition, and verification issues",
  "The 11 incorrect full-text mappings and both original Oxford HTTP 403 issues are preserved here. Access restrictions were not bypassed.",
  accessColumns,
  qa.accessIssues,
  { freezeColumns: 2, rowHeight: 84 },
);
styleStatusColumn(accessResult.sheet, findCol(accessColumns, "resolutionStatus"), accessResult.endRow);

const rejectedColumns = [
  column("source", "Rejected or deferred candidate", 58),
  column("reason", "Original decision reason", 54),
  column("qaDisposition", "QA disposition", 34),
];
const rejectedRows = qa.rejectedCandidates.map((row) => ({
  ...row,
  qaDisposition: "Preserved; not re-researched in this bounded QA pass",
}));
addDataSheet(
  "Rejected Candidates",
  "Rejected and deferred source candidates",
  "Original candidate exclusions are preserved. This QA task did not conduct broad new research or reconsider the source cap.",
  rejectedColumns,
  rejectedRows,
  { rowHeight: 60 },
);

const summarySheet = workbook.worksheets.add("QA Summary");
summarySheet.showGridLines = false;
summarySheet.getRange("A1:F1").merge();
summarySheet.getRange("A1").values = [["IBD evidence QA — approval preparation"]];
summarySheet.getRange("A2:F2").merge();
summarySheet.getRange("A2").values = [[
  "Status: pending human review. No source or claim is approved. Complete decisions in the yellow columns on Sources and Claims.",
]];
summarySheet.getRange("A1:F1").format = {
  fill: palette.navy,
  font: { bold: true, color: palette.white, size: 18 },
  verticalAlignment: "center",
};
summarySheet.getRange("A2:F2").format = {
  fill: palette.pale,
  font: { italic: true, color: palette.ink, size: 11 },
  wrapText: true,
};
summarySheet.getRange("A1").format.rowHeight = 32;
summarySheet.getRange("A2").format.rowHeight = 46;
summarySheet.getRange("A4:C4").values = [["Metric", "Value", "Interpretation"]];
summarySheet.getRange("A4:C4").format = {
  fill: palette.blue,
  font: { bold: true, color: palette.white },
};

const sourceEnd = qa.sources.length + 4;
const claimEnd = qa.claims.length + 4;
const conflictEnd = qa.conflicts.length + 4;
const coverageEnd = qa.coverage.length + 4;
const accessEnd = qa.accessIssues.length + 4;
const abstractEnd = qa.abstractOnlyReview.length + 4;
const sourceQaLetter = findCol(sourcesColumns, "qaStatus");
const claimQaLetter = findCol(claimsColumns, "qaStatus");
const conflictPrimaryLetter = findCol(conflictColumns, "primaryClassification");
const coverageGapLetter = findCol(coverageColumns, "gapClassification");
const accessResolutionLetter = findCol(accessColumns, "resolutionStatus");
const abstractBecameLetter = findCol(abstractColumns, "fullTextBecameAvailable");

const metrics = [
  ["Total sources", `=COUNTA('Sources'!$A$5:$A$${sourceEnd})`, "Selected source records preserved"],
  ["Ready sources", `=COUNTIF('Sources'!$${sourceQaLetter}$5:$${sourceQaLetter}$${sourceEnd},"ready_for_review")`, "Still require human approval"],
  ["Sources needing verification", `=COUNTIF('Sources'!$${sourceQaLetter}$5:$${sourceQaLetter}$${sourceEnd},"needs_verification")+COUNTIF('Sources'!$${sourceQaLetter}$5:$${sourceQaLetter}$${sourceEnd},"insufficient_access")+COUNTIF('Sources'!$${sourceQaLetter}$5:$${sourceQaLetter}$${sourceEnd},"superseded")`, "Includes insufficient access and superseded review"],
  ["Reject-recommended sources", `=COUNTIF('Sources'!$${sourceQaLetter}$5:$${sourceQaLetter}$${sourceEnd},"reject_recommended")`, "No automatic rejection"],
  ["Total claims", `=COUNTA('Claims'!$A$5:$A$${claimEnd})`, "Original claim IDs preserved"],
  ["Ready claims", `=COUNTIF('Claims'!$${claimQaLetter}$5:$${claimQaLetter}$${claimEnd},"ready_for_review")`, "Still require human approval"],
  ["Revision-recommended claims", `=COUNTIF('Claims'!$${claimQaLetter}$5:$${claimQaLetter}$${claimEnd},"wording_revision_recommended")`, "Original wording preserved beside proposal"],
  ["Claims needing more evidence", `=COUNTIF('Claims'!$${claimQaLetter}$5:$${claimQaLetter}$${claimEnd},"needs_more_evidence")`, "Do not approve without resolving evidence gap"],
  ["Reject-recommended claims", `=COUNTIF('Claims'!$${claimQaLetter}$5:$${claimQaLetter}$${claimEnd},"reject_recommended")`, "Methods/background/unsafe or non-atomic statements"],
  ["True conflicts", `=COUNTIF('Conflict Review'!$${conflictPrimaryLetter}$5:$${conflictPrimaryLetter}$${conflictEnd},"true_conflict")`, "No opposing findings identified in the 80 generated flags"],
  ["Non-comparable flags", `=COUNTA('Conflict Review'!$A$5:$A$${conflictEnd})-B14`, "All original flags retained and classified"],
  ["Abstract-only sources remaining", `=COUNTIF('Abstract-Only Review'!$${abstractBecameLetter}$5:$${abstractBecameLetter}$${abstractEnd},"No")`, "From the original set of nine"],
  ["Unresolved access issues", `=COUNTIF('Access and Verification Issues'!$${accessResolutionLetter}$5:$${accessResolutionLetter}$${accessEnd},"unresolved")`, "Includes SRC-013 after correcting its bad mapping"],
  ["Evidence gaps", `=COUNTA('Coverage Matrix'!$A$5:$A$${coverageEnd})-COUNTIF('Coverage Matrix'!$${coverageGapLetter}$5:$${coverageGapLetter}$${coverageEnd},"acceptable_for_mvp")`, "Requires answer limitation, future research, or feature block"],
  ["MVP-blocking gaps", `=COUNTIF('Coverage Matrix'!$${coverageGapLetter}$5:$${coverageGapLetter}$${coverageEnd},"blocks_feature_scope")`, "Blocks only the named feature scope"],
];
const metricEnd = 4 + metrics.length;
summarySheet.getRange(`A5:A${metricEnd}`).values = metrics.map((m) => [m[0]]);
summarySheet.getRange(`B5:B${metricEnd}`).formulas = metrics.map((m) => [m[1]]);
summarySheet.getRange(`C5:C${metricEnd}`).values = metrics.map((m) => [m[2]]);
summarySheet.getRange(`A5:C${metricEnd}`).format = {
  wrapText: true,
  verticalAlignment: "center",
  borders: { insideHorizontal: { style: "thin", color: "#D6DEE5" } },
};
summarySheet.getRange(`A5:A${metricEnd}`).format.font = { bold: true, color: palette.navy };
summarySheet.getRange(`B5:B${metricEnd}`).format = {
  fill: palette.cream,
  font: { bold: true, color: palette.navy, size: 12 },
  numberFormat: "0",
};
summarySheet.getRange(`A5:C${metricEnd}`).format.rowHeight = 34;
summarySheet.getRange("A:A").format.columnWidth = 34;
summarySheet.getRange("B:B").format.columnWidth = 18;
summarySheet.getRange("C:C").format.columnWidth = 62;
summarySheet.freezePanes.freezeRows(4);

summarySheet.getRange("E4:F4").values = [["Critical QA finding", "Impact"]];
summarySheet.getRange("E4:F4").format = {
  fill: palette.red,
  font: { bold: true, color: "#842029" },
};
summarySheet.getRange("E5:F8").values = [
  ["11 incorrect full-text mappings", "Every original public-full-text DOI/PMCID mapping was wrong or invalid. Correct access routes are in Sources."],
  ["2 Oxford 403 issues resolved", "Retained passages are directly verifiable on authoritative pages without bypassing restrictions."],
  ["2017 ESPEN guideline superseded", "Do not approve as current guidance without comparison to the 2023 update."],
  ["Human decisions", "All user decision, edited-claim, notes, and reviewer-note fields are blank."],
];
summarySheet.getRange("E5:F8").format = {
  wrapText: true,
  verticalAlignment: "top",
  borders: { insideHorizontal: { style: "thin", color: "#D6DEE5" } },
};
summarySheet.getRange("E:E").format.columnWidth = 32;
summarySheet.getRange("F:F").format.columnWidth = 62;
summarySheet.getRange("E5:F8").format.rowHeight = 58;

const previewDir = path.join(root, "previews/qa");
await fs.mkdir(previewDir, { recursive: true });
const sheetNames = [
  "Sources",
  "Claims",
  "Conflict Review",
  "Coverage Matrix",
  "Abstract-Only Review",
  "Access and Verification Issues",
  "Rejected Candidates",
  "QA Summary",
];
const verification = { sheets: [], formulaErrors: "", keyRanges: {} };
for (const sheetName of sheetNames) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 0.7, format: "png" });
  const outPath = path.join(previewDir, `${sheetName.replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()}.png`);
  await fs.writeFile(outPath, new Uint8Array(await preview.arrayBuffer()));
  verification.sheets.push({ sheetName, preview: outPath });
}
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
verification.formulaErrors = errors.ndjson;
for (const [sheetName, range] of Object.entries({
  Sources: `A1:${sourceNotesCol}9`,
  Claims: `A1:${claimNotesCol}9`,
  "Conflict Review": "A1:R9",
  "Coverage Matrix": "A1:E20",
  "QA Summary": "A1:F20",
})) {
  const inspected = await workbook.inspect({
    kind: "table",
    range: `${sheetName}!${range}`,
    include: "values,formulas",
    tableMaxRows: 20,
    tableMaxCols: 45,
  });
  verification.keyRanges[sheetName] = inspected.ndjson;
}
await fs.writeFile(path.join(root, "logs/qa-workbook-verification.json"), JSON.stringify(verification, null, 2));

const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(root, "ibd-evidence-review-qa.xlsx");
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, sheetCount: sheetNames.length, previewDir, formulaErrors: errors.ndjson }));
