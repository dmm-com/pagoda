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
import { useTranslation } from "hooks/useTranslation";
import { translate } from "i18n/config";
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
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleRestore = useCallback(
    async (historyId: number) => {
      try {
        await aironeApiClient.restoreEntrySelfHistory(entryId, historyId);
        enqueueSnackbar(translate("entry.selfHistory.restoreSuccess"), {
          variant: "success",
        });
        navigate(topPath(), { replace: true });
        navigate(showEntryHistoryPath(entityId, entryId), { replace: true });
      } catch (e) {
        enqueueSnackbar(translate("entry.selfHistory.restoreFailure"), {
          variant: "error",
        });
      }
    },
    [entryId, entityId, enqueueSnackbar, navigate],
  );

  const getHistoryTypeLabel = (historyType: string): string => {
    switch (historyType) {
      case "+":
        return t("common.create");
      case "~":
        return t("common.update");
      case "-":
        return t("common.delete");
      default:
        return t("common.unknown");
    }
  };

  return (
    <>
      <Table id="table_self_history_list">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="120px">
              {t("entry.selfHistory.operationHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="200px">
              {t("entry.selfHistory.beforeNameHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="200px">
              {t("entry.selfHistory.afterNameHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="120px">
              {t("entry.history.executedAtHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="100px">
              {t("entry.history.executedByHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="60px">
              {t("common.restore")}
            </HeaderTableCell>
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
                      disabled={index === 0} // the latest state (index 0) cannot be restored
                    >
                      <RestoreIcon />
                    </IconButton>
                  )}
                  dialogTitle={t("entry.selfHistory.confirmRestore", {
                    name: history.name,
                  })}
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
