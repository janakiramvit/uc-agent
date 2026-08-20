import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "/Users/janakirampulipati/ibd-research-review";
const data = JSON.parse(await fs.readFile(path.join(root, "processing/remediation/remediation-data.json"), "utf8"));
const workbook = Workbook.create();

const colors = {
  navy: "#17324D", blue: "#2E6882", teal: "#2E7D73", pale: "#EAF3F4",
  cream: "#F7F3EA", yellow: "#FFF2B2", red: "#F8D7DA", amber: "#FCE5B3",
  green: "#DDEFE2", gray: "#E5E7EB", white: "#FFFFFF", ink: "#1F2937",
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
function col(key, header, width = 18) { return { key, header, width }; }
function colLetter(columns, key) { return letters(columns.findIndex(c => c.key === key) + 1); }

function addSheet(name, title, subtitle, columns, rows, options = {}) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  const last = letters(columns.length);
  sheet.getRange(`A1:${last}1`).merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A2:${last}2`).merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A1:${last}1`).format = {
    fill: colors.navy, font: { bold: true, color: colors.white, size: 16 }, verticalAlignment: "center",
  };
  sheet.getRange(`A2:${last}2`).format = {
    fill: colors.pale, font: { italic: true, color: colors.ink, size: 10 }, wrapText: true, verticalAlignment: "center",
  };
  sheet.getRange("A1").format.rowHeight = 31;
  sheet.getRange("A2").format.rowHeight = 44;
  sheet.getRange(`A4:${last}4`).values = [columns.map(c => c.header)];
  sheet.getRange(`A4:${last}4`).format = {
    fill: colors.blue, font: { bold: true, color: colors.white, size: 10 },
    wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: colors.navy },
  };
  sheet.getRange(`A4:${last}4`).format.rowHeight = 40;
  const end = 4 + rows.length;
  if (rows.length) {
    sheet.getRange(`A5:${last}${end}`).values = rows.map(row => columns.map(c => value(row[c.key])));
    sheet.getRange(`A5:${last}${end}`).format = {
      font: { color: colors.ink, size: 9 }, wrapText: true, verticalAlignment: "top",
      borders: { insideHorizontal: { style: "thin", color: "#D6DEE5" } },
    };
    sheet.getRange(`A5:${last}${end}`).format.rowHeight = options.rowHeight || 68;
    const table = sheet.tables.add(`A4:${last}${end}`, true, `${name.replace(/[^A-Za-z0-9]/g, "")}Table`);
    table.style = "TableStyleMedium2";
    table.showFilterButton = true;
    table.showBandedRows = true;
  }
  columns.forEach((c, i) => { sheet.getRange(`${letters(i + 1)}:${letters(i + 1)}`).format.columnWidth = c.width; });
  sheet.freezePanes.freezeRows(4);
  if (options.freezeColumns) sheet.freezePanes.freezeColumns(options.freezeColumns);
  for (const key of options.humanFields || []) {
    const letter = colLetter(columns, key);
    if (letter && rows.length) sheet.getRange(`${letter}5:${letter}${end}`).format.fill = colors.yellow;
  }
  if (options.statusField && rows.length) {
    const letter = colLetter(columns, options.statusField);
    const range = sheet.getRange(`${letter}5:${letter}${end}`);
    for (const [text, fill, font] of [
      ["verified", colors.green, "#155724"], ["ready", colors.green, "#155724"],
      ["partial", colors.amber, "#7A4A00"], ["needs", colors.amber, "#7A4A00"],
      ["unresolved", colors.red, "#842029"], ["superseded", colors.red, "#842029"],
      ["removed", colors.red, "#842029"],
    ]) range.conditionalFormats.add("containsText", { text, format: { fill, font: { bold: true, color: font } } });
  }
  return { sheet, end, columns };
}

const sourceColumns = [
  col("sourceId", "Source ID", 12), col("sourceStatus", "Source status", 24),
  col("sourceTitle", "Source title", 44), col("sourceType", "Source type", 16),
  col("authors", "Authors", 40), col("issuingOrganisation", "Issuing organisation", 28),
  col("journal", "Journal", 24), col("publicationYear", "Year", 10),
  col("sourceUrl", "Source URL", 38), col("canonicalUrl", "Canonical URL", 38),
  col("correctedPmid", "Corrected PMID", 14), col("correctedPmcid", "Corrected PMCID", 17),
  col("correctedDoi", "Corrected DOI", 28), col("fullTextVerification", "Full-text verification", 34),
  col("alternativeAccessUrl", "Authoritative access URL", 40),
  col("supersededBySourceId", "Superseded by", 15), col("conditionApplicability", "Condition applicability", 27),
  col("diseaseContext", "Disease context", 27), col("studyType", "Study type", 23),
  col("population", "Population", 32), col("mainRelevantFinding", "Main relevant finding", 46),
  col("reliabilityLimitations", "Evidence/reliability limitations", 44),
  col("licensingAccessNote", "Access/licensing note", 38), col("applicabilityRegion", "Region assessed", 22),
  col("canadaUsApplicability", "Canada/US applicability", 25), col("regionalAssessment", "Regional assessment", 44),
  col("humanReviewStatus", "Review status", 23), col("userDecision", "User decision", 22),
  col("userNotes", "User notes", 38),
];
const sourcesResult = addSheet(
  "Sources", "IBD evidence sources — remediated",
  "All records remain pending human review. Corrected identifiers and legal-access status are shown; the superseded 2017 source remains for audit history. Yellow fields are intentionally blank.",
  sourceColumns, data.sources, { freezeColumns: 2, rowHeight: 82, humanFields: ["userDecision", "userNotes"], statusField: "sourceStatus" },
);

const claimColumns = [
  col("claimId", "Claim ID", 12), col("sourceId", "Source ID", 12), col("replacesClaimId", "Replaces claim", 15),
  col("sourceTitle", "Source title", 38), col("topic", "Topic", 23), col("conditionApplicability", "Condition applicability", 25),
  col("diseaseContext", "Disease context", 25), col("originalClaim", "Original claim", 50),
  col("qaProposedClaim", "QA proposed claim", 50), col("remediatedClaim", "Remediated claim", 58),
  col("remediationReason", "Remediation reason", 46), col("revisionReason", "Revision reason", 46),
  col("supportingExcerpt", "Supporting excerpt", 58), col("exactLocator", "Exact locator", 46),
  col("evidenceLevel", "Evidence level", 21), col("evidenceStrength", "Evidence strength", 22),
  col("studyType", "Study type", 21), col("population", "Population", 30), col("sampleSize", "Sample size", 18),
  col("limitations", "Limitations", 42), col("applicabilityLimitations", "Applicability limitations", 42),
  col("canadaUsApplicability", "Canada/US applicability", 25), col("confidence", "Confidence", 15),
  col("evidenceStatus", "Evidence status", 25), col("humanReviewStatus", "Review status", 23),
  col("userDecision", "User decision", 22), col("userEditedClaim", "User-edited claim", 50),
  col("reviewerNotes", "Reviewer notes", 38),
];
const claimsResult = addSheet(
  "Claims", "IBD evidence claims — remediated",
  "Contains only evidence-ready claims and the one explicitly marked as still needing evidence, plus two new claims replacing superseded-source statements. No claim is approved.",
  claimColumns, data.claims, { freezeColumns: 3, rowHeight: 92, humanFields: ["userDecision", "userEditedClaim", "reviewerNotes"], statusField: "evidenceStatus" },
);

const mappingColumns = [
  col("sourceId", "Source ID", 12), col("pmid", "PMID", 13), col("sourceTitle", "Verified title", 44),
  col("verifiedFirstAuthor", "Verified first author", 26), col("publicationYear", "Year", 10),
  col("incorrectDoi", "Incorrect DOI", 28), col("incorrectPmcid", "Incorrect PMCID", 18),
  col("correctedDoi", "Corrected DOI", 28), col("correctedPmcid", "Corrected PMCID", 18),
  col("identifierConsistency", "Identifier consistency", 20), col("titleMatch", "Title match", 14),
  col("authorMatch", "Author match", 14), col("yearMatch", "Year match", 14),
  col("wrongMappingRejected", "Wrong mapping rejected", 22), col("incorrectFileArchivedAt", "Incorrect file archive", 45),
  col("correctPublicCopy", "Correct public copy", 46), col("auditOutcome", "Audit outcome", 28),
  col("humanReviewStatus", "Review status", 23),
];
addSheet(
  "Source Mapping Audit", "Source mapping audit — 11 corrected records",
  "Each rejected DOI/PMCID pairing is retained beside the corrected identity and archive location. No incorrect full text remains in the active evidence set.",
  mappingColumns, data.sourceMappingAudit, { freezeColumns: 2, rowHeight: 78, statusField: "auditOutcome" },
);

const removedColumns = [
  col("originalClaimId", "Original claim ID", 16), col("originalSourceId", "Original source ID", 16),
  col("originalClaim", "Original claim", 58), col("accountingCategory", "Accounting category", 22),
  col("replacementClaimId", "Replacement claim ID", 20), col("replacementSourceId", "Replacement source ID", 20),
  col("reason", "Removal/replacement reason", 52), col("archivedAt", "Archive path", 48),
  col("humanReviewStatus", "Review status", 23),
];
addSheet(
  "Removed and Replaced Claims", "Removed and replaced claims — complete audit trail",
  "Thirty-seven claims are removed and two are replaced. Original wording and IDs remain preserved; nothing was permanently deleted.",
  removedColumns, data.removedAndReplacedClaims, { freezeColumns: 2, rowHeight: 82, statusField: "accountingCategory" },
);

const supersededColumns = [
  col("oldSourceId", "Old source ID", 14), col("oldTitle", "Superseded title", 50),
  col("oldPmid", "Old PMID", 14), col("oldDoi", "Old DOI", 28),
  col("supersededReason", "Superseded reason", 42), col("newSourceId", "New source ID", 14),
  col("newTitle", "Replacement title", 50), col("newPmid", "New PMID", 14), col("newDoi", "New DOI", 28),
  col("oldClaimDisposition", "Old-claim disposition", 52), col("archivedAt", "Archive path", 48),
  col("humanReviewStatus", "Review status", 23),
];
addSheet(
  "Superseded Sources", "Superseded sources — replacement map",
  "The 2017 ESPEN guideline is retained only for provenance and mapped to the official 2023 update. Human approval remains pending.",
  supersededColumns, data.supersededSources, { rowHeight: 88, statusField: "supersededReason" },
);

const gapColumns = [
  col("gapId", "Gap ID", 26), col("status", "Resolution status", 42), col("searchCount", "Searches", 12),
  col("candidateCount", "Candidates", 13), col("selectedCount", "Selected", 12),
  col("selectedSources", "Selected sources", 28), col("safeAnswerLimit", "Safe answer limit", 58),
  col("supportingExcerpt", "Supporting excerpt", 58), col("exactLocator", "Exact locator", 48),
  col("reason", "Evidence decision", 48),
];
addSheet(
  "Evidence Gap Resolution", "MVP evidence gaps — bounded resolution",
  "Search caps were enforced separately from claim searches: no more than 3 searches, 4 candidates, or 2 selected sources per gap.",
  gapColumns, data.evidenceGapResolution, { freezeColumns: 2, rowHeight: 100, statusField: "status" },
);

const issueRows = [
  ...data.verificationAndAccessIssues,
  ...data.claimSearchLog.map(x => ({
    issueId: `CLAIM-SEARCH-${x.claimId}-${x.searchNumber}`, sourceId: x.claimId, issueType: "claim_search_budget",
    resolutionStatus: x.outcome, verifiedAccess: x.query, authoritativeUrl: x.candidate,
    claimHandling: `Selected: ${x.selected}`, licensingNote: "Public-source search only; no paywall bypass.", humanReviewStatus: "pending_human_review",
  })),
  ...data.gapSearchLog.map(x => ({
    issueId: `GAP-SEARCH-${x.gapId}-${x.searchNumber}`, sourceId: x.gapId, issueType: "gap_search_budget",
    resolutionStatus: x.selected ? "candidate_selected" : "no_candidate_selected", verifiedAccess: x.query,
    authoritativeUrl: x.candidates, claimHandling: `Selected: ${x.selected || "none"}`,
    licensingNote: "Public-source search only; no paywall bypass.", humanReviewStatus: "pending_human_review",
  })),
];
const issueColumns = [
  col("issueId", "Issue/log ID", 24), col("sourceId", "Source/claim/gap ID", 22),
  col("issueType", "Issue type", 26), col("resolutionStatus", "Resolution status", 36),
  col("verifiedAccess", "Verification/query", 48), col("authoritativeUrl", "Authoritative URL/candidates", 52),
  col("claimHandling", "Claim/selection handling", 48), col("licensingNote", "Access/licensing note", 42),
  col("humanReviewStatus", "Review status", 23),
];
addSheet(
  "Verification and Access Issues", "Verification, access, and bounded-search log",
  "Four legal-access issues remain unresolved. Claim-search and gap-search budgets are logged separately in the same audit sheet.",
  issueColumns, issueRows, { freezeColumns: 2, rowHeight: 76, statusField: "resolutionStatus" },
);

const summarySheet = workbook.worksheets.add("Remediation Summary");
summarySheet.showGridLines = false;
summarySheet.getRange("A1:F1").merge();
summarySheet.getRange("A1").values = [["IBD evidence remediation — approval preparation"]];
summarySheet.getRange("A2:F2").merge();
summarySheet.getRange("A2").values = [["Status: pending second independent QA and human approval. No source or claim has been approved. Human-review fields are blank."]];
summarySheet.getRange("A1:F1").format = { fill: colors.navy, font: { bold: true, color: colors.white, size: 18 } };
summarySheet.getRange("A2:F2").format = { fill: colors.pale, font: { italic: true, color: colors.ink, size: 11 }, wrapText: true };
summarySheet.getRange("A1").format.rowHeight = 34;
summarySheet.getRange("A2").format.rowHeight = 46;
summarySheet.getRange("A4:C4").values = [["Metric", "Value", "Interpretation"]];
summarySheet.getRange("A4:C4").format = { fill: colors.blue, font: { bold: true, color: colors.white } };
const metrics = [
  ["Active sources", 25, "24 retained original sources plus SRC-026; excludes superseded SRC-003"],
  ["Source rows incl. superseded", `=COUNTA('Sources'!$A$5:$A$${sourcesResult.end})`, "Audit-complete source table"],
  ["Incorrect mappings corrected", `=COUNTA('Source Mapping Audit'!$A$5:$A$15)`, "All 11 known mismatches rejected and archived"],
  ["Unresolved access issues", 4, "SRC-002, SRC-013, SRC-015, SRC-017 remain abstract-only"],
  ["Original claims reconciled", 95, "Exact mutually exclusive accounting"],
  ["Retained unchanged", 2, "Ready for human review, not approved"],
  ["Retained revised", 53, "Original and revised wording remain traceable"],
  ["Removed", 37, "Archived with reasons"],
  ["Replaced by new", 2, "CLM-010/011 replaced by CLM-096/097"],
  ["Still needs evidence", 1, "CLM-092 remains explicitly limited"],
  ["Active claim rows", `=COUNTA('Claims'!$A$5:$A$${claimsResult.end})`, "Includes two new replacement claims"],
  ["Resolved MVP gaps", 1, "Physical activity, with bounded wording"],
  ["Partially resolved gaps", 4, "Answer limits are mandatory"],
  ["Excluded MVP feature gaps", 1, "Biomarker claims must be excluded"],
];
summarySheet.getRange(`A5:A${4 + metrics.length}`).values = metrics.map(x => [x[0]]);
const formulas = metrics.map(x => [typeof x[1] === "string" && x[1].startsWith("=") ? x[1] : `=${x[1]}`]);
summarySheet.getRange(`B5:B${4 + metrics.length}`).formulas = formulas;
summarySheet.getRange(`C5:C${4 + metrics.length}`).values = metrics.map(x => [x[2]]);
summarySheet.getRange(`A5:C${4 + metrics.length}`).format = {
  wrapText: true, verticalAlignment: "center", borders: { insideHorizontal: { style: "thin", color: "#D6DEE5" } },
};
summarySheet.getRange(`A5:A${4 + metrics.length}`).format.font = { bold: true, color: colors.navy };
summarySheet.getRange(`B5:B${4 + metrics.length}`).format = { fill: colors.cream, font: { bold: true, color: colors.navy, size: 12 }, numberFormat: "0" };
summarySheet.getRange(`A5:C${4 + metrics.length}`).format.rowHeight = 36;
summarySheet.getRange("A:A").format.columnWidth = 34;
summarySheet.getRange("B:B").format.columnWidth = 18;
summarySheet.getRange("C:C").format.columnWidth = 64;
summarySheet.getRange("E4:F4").values = [["Hard-stop control", "Current state"]];
summarySheet.getRange("E4:F4").format = { fill: colors.red, font: { bold: true, color: "#842029" } };
summarySheet.getRange("E5:F10").values = [
  ["Clinical approval", "Not granted; all evidence remains pending human review."],
  ["Second independent QA", "Required before approval or production use."],
  ["Review fields", "Blank on Sources and Claims."],
  ["Canada/US applicability", "Assessed per source; regional qualification retained."],
  ["Access/licensing", "No paywall bypass; reuse licensing not assumed."],
  ["Architecture/production", "No application, retrieval, API, UI, or infrastructure work performed."],
];
summarySheet.getRange("E5:F10").format = { wrapText: true, verticalAlignment: "top", borders: { insideHorizontal: { style: "thin", color: "#D6DEE5" } } };
summarySheet.getRange("E:E").format.columnWidth = 34;
summarySheet.getRange("F:F").format.columnWidth = 66;
summarySheet.getRange("E5:F10").format.rowHeight = 56;
summarySheet.freezePanes.freezeRows(4);

const sheetNames = [
  "Sources", "Claims", "Source Mapping Audit", "Removed and Replaced Claims",
  "Superseded Sources", "Evidence Gap Resolution", "Verification and Access Issues", "Remediation Summary",
];
const output = await SpreadsheetFile.exportXlsx(workbook);
const outputPath = path.join(root, "ibd-evidence-review-remediated.xlsx");
await output.save(outputPath);

const previewDir = path.join(root, "previews-remediated");
await fs.mkdir(previewDir, { recursive: true });
const verification = { sheets: [], formulaErrors: "", inspections: {} };
for (const sheetName of sheetNames) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 0.6, format: "png" });
  const previewPath = path.join(previewDir, `${sheetName.replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()}.png`);
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
  verification.sheets.push({ sheetName, preview: previewPath });
}
const errors = await workbook.inspect({
  kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 }, summary: "remediated workbook formula-error scan",
});
verification.formulaErrors = errors.ndjson;
for (const [sheetName, range] of Object.entries({
  Sources: "A1:AC9", Claims: "A1:AB9", "Source Mapping Audit": "A1:R15",
  "Removed and Replaced Claims": "A1:I12", "Superseded Sources": "A1:L6",
  "Evidence Gap Resolution": "A1:J10", "Verification and Access Issues": "A1:I14",
  "Remediation Summary": "A1:F18",
})) {
  const inspected = await workbook.inspect({ kind: "table", range: `${sheetName}!${range}`, include: "values,formulas", tableMaxRows: 20, tableMaxCols: 32 });
  verification.inspections[sheetName] = inspected.ndjson;
}
await fs.writeFile(path.join(root, "logs/remediation/workbook-verification.json"), JSON.stringify(verification, null, 2));
console.log(JSON.stringify({ outputPath, sheetCount: sheetNames.length, previewDir, formulaErrors: errors.ndjson }));
