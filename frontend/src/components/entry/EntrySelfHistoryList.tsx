import RestoreIcon from "@mui/icons-material/Restore";
import {
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import { FC, useCallback } from "react";
import { useNavigate } from "react-router";

import { Confirmable } from "components/common/Confirmable";
import { PaginationFooter } from "components/common/PaginationFooter";
import { aironeApiClient } from "repository/AironeApiClient";
import { showEntryHistoryPath, topPath } from "routes/Routes";
import { EntryHistoryListParam } from "services/Constants";
import { formatDateTime } from "services/DateUtil";

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
}));

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "& td": {
    padding: "8px 16px",
  },
}));

interface EntrySelfHistory {
  history_id: number;
  name: string;
  prev_name: string | null;
  history_date: string;
  history_user: string;
  history_type: string;
}

interface PaginatedEntrySelfHistoryList {
  count?: number;
  results?: EntrySelfHistory[];
}

interface Props {
  entityId: number;
  entryId: number;
  histories: PaginatedEntrySelfHistoryList;
  page: number;
  changePage: (page: number) => void;
}

export const EntrySelfHistoryList: FC<Props> = ({
  entityId,
  entryId,
  histories,
  page,
  changePage,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleRestore = useCallback(
    async (historyId: number) => {
      try {
        await aironeApiClient.restoreEntrySelfHistory(entryId, historyId);
        enqueueSnackbar(`アイテム名の復旧が完了しました`, {
          variant: "success",
        });
        navigate(topPath(), { replace: true });
        navigate(showEntryHistoryPath(entityId, entryId), { replace: true });
      } catch (e) {
        enqueueSnackbar(`アイテム名の復旧が失敗しました`, {
          variant: "error",
        });
      }
    },
    [entryId, entityId, enqueueSnackbar, navigate],
  );

  const getHistoryTypeLabel = (historyType: string): string => {
    switch (historyType) {
      case "+":
        return "作成";
      case "~":
        return "更新";
      case "-":
        return "削除";
      default:
        return "不明";
    }
  };

  return (
    <>
      <Table id="table_self_history_list">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="120px">操作</HeaderTableCell>
            <HeaderTableCell width="200px">変更前のアイテム名</HeaderTableCell>
            <HeaderTableCell width="200px">変更後のアイテム名</HeaderTableCell>
            <HeaderTableCell width="120px">実行日時</HeaderTableCell>
            <HeaderTableCell width="100px">実行者</HeaderTableCell>
            <HeaderTableCell width="60px">復旧</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>

        <TableBody>
          {histories.results?.map((history, index) => (
            <StyledTableRow key={history.history_id}>
              <TableCell>
                <Typography variant="body2" fontWeight="bold">
                  {getHistoryTypeLabel(history.history_type)}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography>{history.prev_name || "-"}</Typography>
              </TableCell>
              <TableCell>
                <Typography fontWeight="bold">{history.name}</Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2">
                  {formatDateTime(new Date(history.history_date))}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="body2">{history.history_user}</Typography>
              </TableCell>
              <TableCell>
                <Confirmable
                  componentGenerator={(handleOpen) => (
                    <IconButton
                      onClick={handleOpen}
                      disabled={index === 0} // 最新の状態（index 0）は復旧不可
                    >
                      <RestoreIcon />
                    </IconButton>
                  )}
                  dialogTitle={`アイテム名を「${history.name}」に復旧しますか？`}
                  onClickYes={() => handleRestore(history.history_id)}
                />
              </TableCell>
            </StyledTableRow>
          ))}
        </TableBody>
      </Table>

      <PaginationFooter
        count={histories.count ?? 0}
        maxRowCount={EntryHistoryListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </>
  );
};
