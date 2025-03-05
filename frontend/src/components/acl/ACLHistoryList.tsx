import { ACLHistory } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

import { AironeTableHeadCell } from "components/common/AironeTableHeadCell";
import { AironeTableHeadRow } from "components/common/AironeTableHeadRow";
import { ACLType, ACLTypeLabels } from "services/Constants";
import { formatDateTime } from "services/DateUtil";

const StyledTableCell = styled(TableCell)(({}) => ({
  width: "200px",
  padding: "8px 0",
  border: "0",
}));

interface Props {
  histories: Array<ACLHistory>;
}

export const ACLHistoryList: FC<Props> = ({ histories }) => {
  return (
    <Box>
      <Table id="table_history_list">
        <TableHead>
          <AironeTableHeadRow>
            <AironeTableHeadCell width="200px"></AironeTableHeadCell>
            <AironeTableHeadCell width="540px">
              <Box display="flex">
                <Typography width="180px">項目</Typography>
                <Typography width="180px">変更前</Typography>
                <Typography width="180px">変更後</Typography>
              </Box>
            </AironeTableHeadCell>
            <AironeTableHeadCell width="140px">実行日時</AironeTableHeadCell>
            <AironeTableHeadCell width="144px">実行者</AironeTableHeadCell>
          </AironeTableHeadRow>
        </TableHead>

        <TableBody>
          {histories.map((history, index) => (
            <TableRow key={index}>
              <TableCell>{history.name}</TableCell>
              <TableCell sx={{ py: "0" }}>
                <Table>
                  <TableBody>
                    {history.changes.map((change) => (
                      <TableRow key={change.target}>
                        {(() => {
                          switch (change.target) {
                            case "is_public":
                              return (
                                <>
                                  <StyledTableCell>公開設定</StyledTableCell>
                                  <StyledTableCell>
                                    {(change.before as boolean | undefined)
                                      ? true
                                        ? "公開"
                                        : "限定公開"
                                      : "-"}
                                  </StyledTableCell>
                                  <StyledTableCell>
                                    {(change.after as boolean)
                                      ? "公開"
                                      : "限定公開"}
                                  </StyledTableCell>
                                </>
                              );
                            default:
                              return (
                                <>
                                  <StyledTableCell>
                                    {change.target == "default_permission"
                                      ? "デフォルト権限"
                                      : change.target}
                                  </StyledTableCell>
                                  <StyledTableCell>
                                    {change.before != null
                                      ? (ACLTypeLabels[
                                          change.before as ACLType
                                        ] ?? "不明")
                                      : "-"}
                                  </StyledTableCell>
                                  <StyledTableCell>
                                    {change.after != null
                                      ? (ACLTypeLabels[
                                          change.after as ACLType
                                        ] ?? "不明")
                                      : "-"}
                                  </StyledTableCell>
                                </>
                              );
                          }
                        })()}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableCell>
              <TableCell>{formatDateTime(history.time)}</TableCell>
              <TableCell>{history.user?.username ?? "-"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
};
