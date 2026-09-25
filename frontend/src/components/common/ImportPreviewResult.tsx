import {
  Box,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { FC, useState } from "react";

import { useTranslation } from "../../hooks/useTranslation";

import { AironeTableHeadCell } from "./AironeTableHeadCell";
import { AironeTableHeadRow } from "./AironeTableHeadRow";
import {
  ImportPreview,
  ImportPreviewAction,
  ImportPreviewRow,
  ImportPreviewSummaryKey,
  importPreviewActionLabel,
  importPreviewSkipReasonLabel,
  isImportPreviewNoop,
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

// Rows the user has to act on come first; unchanged rows are the least urgent.
const ActionOrder: ImportPreviewAction[] = [
  "error",
  "skip",
  "create",
  "update",
  "unchanged",
];

interface Props {
  preview: ImportPreview;
  /** Selected actions, or an empty array for "everything". */
  actions: ImportPreviewAction[];
  onChangeActions: (actions: ImportPreviewAction[]) => void;
  onLoadMore: () => void;
  onDownload?: () => void;
  loading: boolean;
}

const changeSummary = (row: ImportPreviewRow): string => {
  if (row.action === "skip" || row.action === "error") {
    return row.reason != null ? importPreviewSkipReasonLabel(row.reason) : "-";
  }

  const changes = row.changes
    .map((change) =>
      row.action === "create"
        ? `${change.field}: ${change.after ?? ""}`
        : `${change.field}: ${change.before ?? ""} → ${change.after ?? ""}`,
    )
    .join(" / ");

  // A row can both change something and carry a warning, e.g. a value that was
  // set alongside a reference that could not be resolved.
  return [changes || "-", row.reason].filter(Boolean).join(" / ");
};

export const ImportPreviewResult: FC<Props> = ({
  preview,
  actions,
  onChangeActions,
  onLoadMore,
  onDownload,
  loading,
}) => {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState<string>();

  const toggleAction = (action: ImportPreviewAction) =>
    onChangeActions(
      actions.includes(action)
        ? actions.filter((x) => x !== action)
        : [...actions, action],
    );

  const remaining = preview.count - preview.rows.length;

  return (
    <Box display="flex" flexDirection="column" data-testid="import-preview">
      <Box display="flex" gap="8px" flexWrap="wrap" my="8px">
        {ActionOrder.filter(
          (action) => preview.summary[ImportPreviewSummaryKey[action]] > 0,
        ).map((action) => (
          <Chip
            key={action}
            color={ActionColor[action]}
            variant={
              actions.length === 0 || actions.includes(action)
                ? "filled"
                : "outlined"
            }
            label={`${importPreviewActionLabel(action)} ${preview.summary[ImportPreviewSummaryKey[action]]}`}
            size="small"
            onClick={() => toggleAction(action)}
            data-testid={`import-preview-filter-${action}`}
          />
        ))}
        <Chip
          label={t("importPreview.total", { count: preview.summary.total })}
          size="small"
        />
      </Box>

      <Typography variant="caption" color="text.secondary" my="4px">
        {actions.length === 0
          ? t("importPreview.filterHintAll")
          : t("importPreview.filterHintSelected")}
      </Typography>

      {isImportPreviewNoop(preview) && (
        <Typography variant="body2" my="4px">
          {t("importPreview.noopMessage")}
        </Typography>
      )}

      <Box maxHeight="320px" overflow="auto">
        <Table size="small">
          <TableHead>
            <AironeTableHeadRow>
              <AironeTableHeadCell sx={{ width: "100px" }}>
                {t("importPreview.columns.action")}
              </AironeTableHeadCell>
              <AironeTableHeadCell sx={{ width: "100px" }}>
                {t("importPreview.columns.kind")}
              </AironeTableHeadCell>
              <AironeTableHeadCell sx={{ width: "160px" }}>
                {t("importPreview.columns.name")}
              </AironeTableHeadCell>
              <AironeTableHeadCell>
                {t("importPreview.columns.changes")}
              </AironeTableHeadCell>
            </AironeTableHeadRow>
          </TableHead>
          <TableBody>
            {preview.rows.map((row) => {
              const key = `${row.kind}-${row.index}`;
              return (
                <TableRow
                  key={key}
                  hover
                  onClick={() =>
                    setExpanded(expanded === key ? undefined : key)
                  }
                  sx={{ cursor: "pointer" }}
                >
                  <TableCell>
                    <Chip
                      color={ActionColor[row.action]}
                      label={importPreviewActionLabel(row.action)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{row.kind}</TableCell>
                  <TableCell>{row.name}</TableCell>
                  <TableCell
                    sx={
                      expanded === key
                        ? undefined
                        : {
                            maxWidth: 0,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }
                    }
                  >
                    {changeSummary(row)}
                  </TableCell>
                </TableRow>
              );
            })}
            {preview.rows.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography variant="body2">
                    {t("importPreview.noRows")}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Box>

      <Box display="flex" alignItems="center" gap="8px" my="4px">
        {remaining > 0 && (
          <Button
            size="small"
            disabled={loading}
            onClick={onLoadMore}
            data-testid="import-preview-load-more"
          >
            {t("importPreview.loadMore", { remaining })}
          </Button>
        )}
        {onDownload && (
          <Button
            size="small"
            onClick={onDownload}
            data-testid="import-preview-download"
          >
            {t("importPreview.downloadCsv")}
          </Button>
        )}
      </Box>

      {preview.truncated && (
        <Typography variant="caption" my="4px">
          {t("importPreview.truncatedNotice", {
            total: preview.summary.total,
          })}
        </Typography>
      )}
    </Box>
  );
};
