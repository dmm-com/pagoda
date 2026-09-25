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
import { FC } from "react";

import { AironeTableHeadCell } from "components/common/AironeTableHeadCell";
import { AironeTableHeadRow } from "components/common/AironeTableHeadRow";
import { useTranslation } from "hooks/useTranslation";
import { ACLType, ACLTypeLabels } from "services/ACLUtil";
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
  const { t } = useTranslation();

  return (
    <Box>
      <Table id="table_history_list">
        <TableHead>
          <AironeTableHeadRow>
            <AironeTableHeadCell width="200px"></AironeTableHeadCell>
            <AironeTableHeadCell width="540px">
              <Box display="flex">
                <Typography width="180px">{t("acl.history.item")}</Typography>
                <Typography width="180px">{t("acl.history.before")}</Typography>
                <Typography width="180px">{t("acl.history.after")}</Typography>
              </Box>
            </AironeTableHeadCell>
            <AironeTableHeadCell width="140px">
              {t("acl.history.time")}
            </AironeTableHeadCell>
            <AironeTableHeadCell width="144px">
              {t("acl.history.user")}
            </AironeTableHeadCell>
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
                                  <StyledTableCell>
                                    {t("acl.history.isPublicLabel")}
                                  </StyledTableCell>
                                  <StyledTableCell>
                                    {(change.before as boolean | undefined)
                                      ? true
                                        ? t("acl.history.public")
                                        : t("acl.history.limitedPublic")
                                      : "-"}
                                  </StyledTableCell>
                                  <StyledTableCell>
                                    {(change.after as boolean)
                                      ? t("acl.history.public")
                                      : t("acl.history.limitedPublic")}
                                  </StyledTableCell>
                                </>
                              );
                            default:
                              return (
                                <>
                                  <StyledTableCell>
                                    {change.target == "default_permission"
                                      ? t("acl.history.defaultPermission")
                                      : change.target}
                                  </StyledTableCell>
                                  <StyledTableCell>
                                    {change.before != null
                                      ? (ACLTypeLabels[
                                          change.before as ACLType
                                        ] ?? t("common.unknown"))
                                      : "-"}
                                  </StyledTableCell>
                                  <StyledTableCell>
                                    {change.after != null
                                      ? (ACLTypeLabels[
                                          change.after as ACLType
                                        ] ?? t("common.unknown"))
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
