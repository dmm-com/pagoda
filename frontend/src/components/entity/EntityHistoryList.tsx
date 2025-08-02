import { PaginatedEntityHistoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
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
                    case TargetOperation.ADD_ATTR:
                      return <Typography />;
                    case TargetOperation.DEL_ATTR:
                      return (
                        <Typography>
                          {history.targetObj.replace(/_deleted_.*/, "")}
                        </Typography>
                      );
                    default:
                      return <Typography>TBD</Typography>;
                  }
                })()}
              </TableCell>
              <TableCell>
                {(() => {
                  switch (history.operation) {
                    case TargetOperation.ADD_ATTR:
                      return <Typography>{history.targetObj}</Typography>;
                    case TargetOperation.MOD_ATTR:
                      return <Typography>{history.targetObj}</Typography>;
                    case TargetOperation.DEL_ATTR:
                      return (
                        <Typography sx={{ textDecoration: "line-through" }}>
                          {history.targetObj.replace(/_deleted_.*/, "")}
                        </Typography>
                      );
                    default:
                      return <Typography>TBD</Typography>;
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
