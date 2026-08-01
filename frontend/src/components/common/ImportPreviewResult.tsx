import {
  Box,
  Chip,
  FormControlLabel,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { FC, useMemo, useState } from "react";

import { AironeTableHeadCell } from "./AironeTableHeadCell";
import { AironeTableHeadRow } from "./AironeTableHeadRow";
import {
  ImportPreview,
  ImportPreviewAction,
  ImportPreviewActionLabel,
  isImportPreviewNoop,
  ImportPreviewRow,
  ImportPreviewSkipReasonLabel,
  ImportPreviewSummaryKey,
} from "./ImportPreview";

const ActionColor: Record<
  ImportPreviewAction,
  "success" | "info" | "default" | "warning" | "error"
> = {
  create: "success",
  update: "info",
  unchanged: "default",
  skip: "warning",
  error: "error",
};

// Rows the user has to act on are listed first; unchanged rows are just noise.
const ActionOrder: ImportPreviewAction[] = [
  "error",
  "skip",
  "create",
  "update",
  "unchanged",
];

// The number of rows rendered at once. A preview of a large file would otherwise
// freeze the browser while the user only ever looks at the first few rows.
const MaxRenderedRows = 200;

interface Props {
  preview: ImportPreview;
}

const changeSummary = (row: ImportPreviewRow): string => {
  if (row.action === "skip" || row.action === "error") {
    return row.reason != null
      ? (ImportPreviewSkipReasonLabel[row.reason] ?? row.reason)
      : "-";
  }
  if (row.changes.length === 0) {
    return "-";
  }
  return row.changes
    .map((change) =>
      row.action === "create"
        ? `${change.field}: ${change.after ?? ""}`
        : `${change.field}: ${change.before ?? ""} → ${change.after ?? ""}`,
    )
    .join(" / ");
};

export const ImportPreviewResult: FC<Props> = ({ preview }) => {
  const [showUnchanged, setShowUnchanged] = useState(false);

  const rows = useMemo(() => {
    const visible = showUnchanged
      ? preview.rows
      : preview.rows.filter((row) => row.action !== "unchanged");
    return [...visible].sort(
      (a, b) => ActionOrder.indexOf(a.action) - ActionOrder.indexOf(b.action),
    );
  }, [preview.rows, showUnchanged]);

  const hiddenCount = rows.length - Math.min(rows.length, MaxRenderedRows);

  return (
    <Box display="flex" flexDirection="column" data-testid="import-preview">
      <Box display="flex" gap="8px" flexWrap="wrap" my="8px">
        {ActionOrder.filter(
          (action) => preview.summary[ImportPreviewSummaryKey[action]] > 0,
        ).map((action) => (
          <Chip
            key={action}
            color={ActionColor[action]}
            label={`${ImportPreviewActionLabel[action]} ${preview.summary[ImportPreviewSummaryKey[action]]}`}
            size="small"
          />
        ))}
        <Chip label={`合計 ${preview.summary.total}`} size="small" />
      </Box>

      {isImportPreviewNoop(preview) && (
        <Typography variant="body2" my="4px">
          このファイルをインポートしても変更は発生しません。
        </Typography>
      )}

      <FormControlLabel
        control={
          <Switch
            size="small"
            checked={showUnchanged}
            onChange={(event) => setShowUnchanged(event.target.checked)}
          />
        }
        label={<Typography variant="body2">変更のない行も表示する</Typography>}
      />

      <Box maxHeight="320px" overflow="auto">
        <Table size="small">
          <TableHead>
            <AironeTableHeadRow>
              <AironeTableHeadCell sx={{ width: "100px" }}>
                操作
              </AironeTableHeadCell>
              <AironeTableHeadCell sx={{ width: "100px" }}>
                種別
              </AironeTableHeadCell>
              <AironeTableHeadCell sx={{ width: "160px" }}>
                名前
              </AironeTableHeadCell>
              <AironeTableHeadCell>変更内容</AironeTableHeadCell>
            </AironeTableHeadRow>
          </TableHead>
          <TableBody>
            {rows.slice(0, MaxRenderedRows).map((row) => (
              <TableRow key={`${row.kind}-${row.index}`}>
                <TableCell>
                  <Chip
                    color={ActionColor[row.action]}
                    label={ImportPreviewActionLabel[row.action]}
                    size="small"
                  />
                </TableCell>
                <TableCell>{row.kind}</TableCell>
                <TableCell>{row.name}</TableCell>
                <TableCell>{changeSummary(row)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Box>

      {hiddenCount > 0 && (
        <Typography variant="caption" my="4px">
          {`ほか ${hiddenCount} 行は省略されています。`}
        </Typography>
      )}
    </Box>
  );
};
