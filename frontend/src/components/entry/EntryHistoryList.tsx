import { PaginatedEntryHistoryAttributeValueList } from "@dmm-com/airone-apiclient-typescript-fetch";
import RestoreIcon from "@mui/icons-material/Restore";
import {
  Box,
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
import { FC, ReactNode, useCallback } from "react";
import { useNavigate } from "react-router";

import { AttributeValue } from "./AttributeValue";

import { Confirmable } from "components/common/Confirmable";
import { PaginationFooter } from "components/common/PaginationFooter";
import { useTranslation } from "hooks/useTranslation";
import { translate } from "i18n/config";
import { aironeApiClient } from "repository/AironeApiClient";
import { showEntryHistoryPath, topPath } from "routes/Routes";
import { EntryHistoryListParam } from "services/Constants";
import { formatDateTime } from "services/DateUtil";

interface WrapperProps {
  children: ReactNode;
}

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

const EntryHistoryValueWrapper: FC<WrapperProps> = ({ children }) => {
  return (
    <Box
      sx={{
        maxWidth: 300,
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        overflowWrap: "break-word",
      }}
    >
      {children}
    </Box>
  );
};

interface Props {
  entityId: number;
  entryId: number;
  histories: PaginatedEntryHistoryAttributeValueList;
  page: number;
  changePage: (page: number) => void;
}

export const EntryHistoryList: FC<Props> = ({
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
    async (prevAttrValueId: number) => {
      try {
        await aironeApiClient.restoreEntryHistory(prevAttrValueId);
        enqueueSnackbar(translate("entry.history.restoreSuccess"), {
          variant: "success",
        });
        navigate(topPath(), { replace: true });
        navigate(showEntryHistoryPath(entityId, entryId), { replace: true });
      } catch (e) {
        enqueueSnackbar(translate("entry.history.restoreFailure"), {
          variant: "error",
        });
      }
    },
    [enqueueSnackbar, entityId, entryId, navigate],
  );

  return (
    <>
      <Table id="table_history_list">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="140px">
              {t("entry.common.itemHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="300px">
              {t("entry.history.beforeHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="300px">
              {t("entry.history.afterHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="80px">
              {t("entry.history.executedAtHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="100px">
              {t("entry.history.executedByHeader")}
            </HeaderTableCell>
            <HeaderTableCell width="40px">
              {t("common.restore")}
            </HeaderTableCell>
          </HeaderTableRow>
        </TableHead>

        <TableBody>
          {histories.results?.map((history) => (
            <StyledTableRow key={history.id}>
              <TableCell>{history.parentAttr.name}</TableCell>
              <TableCell>
                <EntryHistoryValueWrapper>
                  {history.prevValue ? (
                    <AttributeValue
                      attrInfo={{
                        type: history.type,
                        value: history.prevValue,
                      }}
                    />
                  ) : (
                    <Typography>-</Typography>
                  )}
                </EntryHistoryValueWrapper>
              </TableCell>
              <TableCell>
                <EntryHistoryValueWrapper>
                  <AttributeValue
                    attrInfo={{
                      type: history.type,
                      value: history.currValue,
                    }}
                  />
                </EntryHistoryValueWrapper>
              </TableCell>
              <TableCell>{formatDateTime(history.createdTime)}</TableCell>
              <TableCell>{history.createdUser}</TableCell>
              <TableCell>
                <Confirmable
                  componentGenerator={(handleOpen) => (
                    <IconButton onClick={handleOpen} disabled={!history.prevId}>
                      <RestoreIcon />
                    </IconButton>
                  )}
                  dialogTitle={t("entry.history.confirmRestoreValue")}
                  onClickYes={() => {
                    if (history.prevId != null) handleRestore(history.prevId);
                  }}
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
