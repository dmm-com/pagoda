import { EntryHistoryAttributeValue } from "@dmm-com/airone-apiclient-typescript-fetch";
import RestoreIcon from "@mui/icons-material/Restore";
import {
  Box,
  IconButton,
  Pagination,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import React, { FC, useCallback } from "react";
import { useHistory } from "react-router-dom";

import { AttributeValue } from "./AttributeValue";

import { showEntryHistoryPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { Confirmable } from "components/common/Confirmable";
import { formatDate } from "services/DateUtil";

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
}));

interface Props {
  histories: Array<EntryHistoryAttributeValue>;
  entryId: number;
  page: number;
  maxPage: number;
  handleChangePage: (page: number) => void;
}

export const EntryHistoryList: FC<Props> = ({
  histories,
  entryId,
  page,
  maxPage,
  handleChangePage,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();

  const handleRestore = useCallback(async (attrValueId: number) => {
    try {
      await aironeApiClientV2.restoreEntryHistory(attrValueId);
      enqueueSnackbar(`変更の復旧が完了しました`, {
        variant: "success",
      });
      history.replace(topPath());
      history.replace(showEntryHistoryPath(entryId));
    } catch (e) {
      enqueueSnackbar(`変更の復旧が失敗しました`, {
        variant: "error",
      });
    }
  }, []);

  return (
    <Box>
      <Table>
        <TableHead>
          <HeaderTableRow>
            <HeaderTableCell>項目</HeaderTableCell>
            <HeaderTableCell>変更前</HeaderTableCell>
            <HeaderTableCell>変更後</HeaderTableCell>
            <HeaderTableCell>実行日時</HeaderTableCell>
            <HeaderTableCell>実行者</HeaderTableCell>
            <HeaderTableCell>復旧</HeaderTableCell>
          </HeaderTableRow>
        </TableHead>

        <TableBody>
          {histories.map((history) => (
            <TableRow key={history.id}>
              <TableCell>{history.parentAttr.name}</TableCell>
              <TableCell>
                {history.prevValue != null && (
                  <AttributeValue
                    attrInfo={{
                      type: history.type,
                      value: history.prevValue,
                    }}
                  />
                )}
              </TableCell>
              <TableCell>
                {history.currValue != null && (
                  <AttributeValue
                    attrInfo={{
                      type: history.type,
                      value: history.currValue,
                    }}
                  />
                )}
              </TableCell>
              <TableCell>{formatDate(history.createdTime)}</TableCell>
              <TableCell>{history.createdUser}</TableCell>
              <TableCell>
                {!history.isLatest && (
                  <Confirmable
                    componentGenerator={(handleOpen) => (
                      <IconButton onClick={handleOpen}>
                        <RestoreIcon />
                      </IconButton>
                    )}
                    dialogTitle={`本当に復旧しますか？`}
                    onClickYes={() => handleRestore(history.id)}
                  />
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Box display="flex" justifyContent="center" my="30px">
        <Stack spacing={2}>
          <Pagination
            count={maxPage}
            page={page}
            onChange={(e, page) => handleChangePage(page)}
            color="primary"
          />
        </Stack>
      </Box>
    </Box>
  );
};
