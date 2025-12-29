import {
  EntityHistoryChange,
  PaginatedEntityHistoryList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { FC } from "react";

import { PaginationFooter } from "components/common/PaginationFooter";
import { EntityHistoryListParam } from "services/Constants";
import { formatDateTime } from "services/DateUtil";

/**
 * Format a single change value for display.
 */
const formatChangeValue = (value: unknown): string => {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
};

/**
 * Format changes for display in the before/after columns.
 */
const formatChanges = (
  changes: EntityHistoryChange[] | undefined,
  type: "before" | "after",
): JSX.Element => {
  if (!changes || changes.length === 0) {
    return <Typography>-</Typography>;
  }

  return (
    <Box>
      {changes.map((change, idx) => (
        <Typography key={idx} variant="body2">
          <strong>{change.target}:</strong>{" "}
          {formatChangeValue(type === "before" ? change.before : change.after)}
        </Typography>
      ))}
    </Box>
  );
};

const Operations = {
  ADD: 1 << 0,
  MOD: 1 << 1,
  DEL: 1 << 2,
};

const Targets = {
  ENTITY: 1 << 3,
  ATTR: 1 << 4,
  ENTRY: 1 << 5,
};

export const TargetOperation = {
  ADD_ENTITY: Operations.ADD + Targets.ENTITY,
  ADD_ATTR: Operations.ADD + Targets.ATTR,
  MOD_ENTITY: Operations.MOD + Targets.ENTITY,
  MOD_ATTR: Operations.MOD + Targets.ATTR,
  DEL_ENTITY: Operations.DEL + Targets.ENTITY,
  DEL_ATTR: Operations.DEL + Targets.ATTR,
  DEL_ENTRY: Operations.DEL + Targets.ENTRY,
};

interface Props {
  histories: PaginatedEntityHistoryList;
  page: number;
  changePage: (page: number) => void;
}

export const EntityHistoryList: FC<Props> = ({
  histories,
  page,
  changePage,
}) => {
  return (
    <Box>
      <Table>
        <TableHead>
          <TableRow sx={{ backgroundColor: "#455A64" }}>
            <TableCell sx={{ color: "#FFFFFF" }}>内容</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>変更前</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>変更後</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>実行日時</TableCell>
            <TableCell sx={{ color: "#FFFFFF" }}>実行者</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {histories.results?.map((history, index) => (
            <TableRow key={index}>
              <TableCell>
                {(() => {
                  switch (history.operation) {
                    case TargetOperation.ADD_ENTITY:
                      return <Typography>作成</Typography>;
                    case TargetOperation.MOD_ENTITY:
                      return <Typography>変更</Typography>;
                    case TargetOperation.DEL_ENTITY:
                      return <Typography>削除</Typography>;
                    case TargetOperation.ADD_ATTR:
                      return <Typography>属性追加</Typography>;
                    case TargetOperation.MOD_ATTR:
                      return <Typography>属性変更</Typography>;
                    case TargetOperation.DEL_ATTR:
                      return <Typography>属性削除</Typography>;
                    default:
                      return (
                        <Typography>
                          {history.operation} ({TargetOperation.ADD_ENTITY})
                        </Typography>
                      );
                  }
                })()}
              </TableCell>
              <TableCell>
                {(() => {
                  switch (history.operation) {
                    case TargetOperation.ADD_ENTITY:
                    case TargetOperation.ADD_ATTR:
                      // No "before" value for create operations
                      return <Typography>-</Typography>;
                    case TargetOperation.DEL_ATTR:
                      return (
                        <Typography>
                          {history.targetObj.replace(/_deleted_.*/, "")}
                        </Typography>
                      );
                    case TargetOperation.MOD_ENTITY:
                    case TargetOperation.DEL_ENTITY:
                    case TargetOperation.MOD_ATTR:
                      // Use changes from simple-history
                      return formatChanges(history.changes, "before");
                    default:
                      return <Typography>-</Typography>;
                  }
                })()}
              </TableCell>
              <TableCell>
                {(() => {
                  switch (history.operation) {
                    case TargetOperation.ADD_ENTITY:
                      // Use changes from simple-history for create
                      return formatChanges(history.changes, "after");
                    case TargetOperation.ADD_ATTR:
                      return <Typography>{history.targetObj}</Typography>;
                    case TargetOperation.MOD_ATTR:
                      // Use changes from simple-history
                      if (history.changes && history.changes.length > 0) {
                        return formatChanges(history.changes, "after");
                      }
                      return <Typography>{history.targetObj}</Typography>;
                    case TargetOperation.DEL_ATTR:
                      return (
                        <Typography sx={{ textDecoration: "line-through" }}>
                          {history.targetObj.replace(/_deleted_.*/, "")}
                        </Typography>
                      );
                    case TargetOperation.MOD_ENTITY:
                    case TargetOperation.DEL_ENTITY:
                      // Use changes from simple-history
                      return formatChanges(history.changes, "after");
                    default:
                      return <Typography>-</Typography>;
                  }
                })()}
              </TableCell>
              <TableCell>{formatDateTime(history.time)}</TableCell>
              <TableCell>{history.username}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <PaginationFooter
        count={histories.count ?? 0}
        maxRowCount={EntityHistoryListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </Box>
  );
};
