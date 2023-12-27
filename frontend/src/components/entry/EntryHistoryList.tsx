import { PaginatedEntryHistoryAttributeValueList } from "@dmm-com/airone-apiclient-typescript-fetch";
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
import React, { FC, useCallback } from "react";
import { useHistory } from "react-router-dom";

import { AttributeValue } from "./AttributeValue";

import { showEntryHistoryPath, topPath } from "Routes";
import { Confirmable } from "components/common/Confirmable";
import { PaginationFooter } from "components/common/PaginationFooter";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";
import { EntryHistoryList as ConstEntryHistoryList } from "services/Constants";
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
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();

  const handleRestore = useCallback(async (prevAttrValueId: number) => {
    try {
      await aironeApiClientV2.restoreEntryHistory(prevAttrValueId);
      enqueueSnackbar(`変更の復旧が完了しました`, {
        variant: "success",
      });
      history.replace(topPath());
      history.replace(showEntryHistoryPath(entityId, entryId));
    } catch (e) {
      enqueueSnackbar(`変更の復旧が失敗しました`, {
        variant: "error",
      });
    }
  }, []);

  return (
    <>
      <Table id="table_history_list">
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell width="140px">項目</HeaderTableCell>
            <HeaderTableCell width="300px">変更前</HeaderTableCell>
            <HeaderTableCell width="300px">変更後</HeaderTableCell>
            <HeaderTableCell width="80px">実行日時</HeaderTableCell>
            <HeaderTableCell width="100px">実行者</HeaderTableCell>
            <HeaderTableCell width="40px">復旧</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>

        <TableBody>
          {histories.results?.map((history) => (
            <StyledTableRow key={history.id}>
              <TableCell>{history.parentAttr.name}</TableCell>
              <TableCell>
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
              </TableCell>
              <TableCell>
                <AttributeValue
                  attrInfo={{
                    type: history.type,
                    value: history.currValue,
                  }}
                />
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
                  dialogTitle={`変更前の値に復旧しますか？`}
                  onClickYes={() =>
                    history.prevId != null && handleRestore(history.prevId)
                  }
                />
              </TableCell>
            </StyledTableRow>
          ))}
        </TableBody>
      </Table>

      <PaginationFooter
        count={histories.count ?? 0}
        maxRowCount={ConstEntryHistoryList.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
    </>
  );
};
