import type { ProcessResponse } from "../types";

/** Mirrors backend/src/exporter.py's to_csv() shape, applied client-side to
 * the already-fetched result so no extra API round-trip is needed to export. */
export function resultToCsv(result: ProcessResponse): string {
  const header = "field,value,confidence,is_present,is_valid,issue";
  const rows = Object.entries(result.fields).map(([name, field]) => {
    const cells = [
      name,
      field.value ?? "",
      field.confidence.toString(),
      String(field.is_present),
      String(field.is_valid),
      field.issue ?? "",
    ];
    return cells
      .map((cell) => (cell.includes(",") || cell.includes('"') ? `"${cell.replace(/"/g, '""')}"` : cell))
      .join(",");
  });
  return [header, ...rows].join("\n");
}

export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function baseFileName(sourceFile: string): string {
  const stem = sourceFile.replace(/\.[^/.]+$/, "");
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  return `${stem}_${timestamp}`;
}
