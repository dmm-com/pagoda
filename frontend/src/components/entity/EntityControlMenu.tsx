import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import {
  aclPath,
  entityHistoryPath,
  entityPath,
  importEntriesPath,
} from "../../Routes";
import { deleteEntity, exportEntries } from "../../utils/AironeAPIClient";
import { Confirmable } from "../common/Confirmable";

type ExportFormatType = "YAML" | "CSV";

interface Props {
  entityId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (entityId: number) => void;
}

export const EntityControlMenu: FC<Props> = ({
  entityId,
  anchorElem,
  handleClose,
}) => {
  const { enqueueSnackbar } = useSnackbar();

  const handleDelete = async (event, entityId: number) => {
    const resp = await deleteEntity(entityId);
    if (resp.ok) {
      enqueueSnackbar("エンティティの削除が成功しました", {
        variant: "success",
      });
    } else {
      enqueueSnackbar("エンティティの削除が失敗しました", { variant: "error" });
    }
    history.go(0);
  };
  const handleExport = async (entityId: number, format: ExportFormatType) => {
    const resp = await exportEntries(entityId, format);
    if (resp.ok) {
      enqueueSnackbar("エンティティのエクスポートのジョブ登録が成功しました", {
        variant: "success",
      });
    } else {
      enqueueSnackbar("エンティティのエクスポートのジョブ登録が失敗しました", {
        variant: "error",
      });
    }
  };

  return (
    <Menu
      id={`entityControlMenu-${entityId}`}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(entityId)}
      anchorEl={anchorElem}
    >
      <MenuItem component={Link} to={entityPath(entityId)}>
        <Typography>編集</Typography>
      </MenuItem>
      <MenuItem component={Link} to={aclPath(entityId)}>
        <Typography>ACL 設定</Typography>
      </MenuItem>
      <MenuItem onClick={handleExport.bind(null, entityId, "YAML")}>
        <Typography>エクスポート(YAML)</Typography>
      </MenuItem>
      <MenuItem onClick={handleExport.bind(null, entityId, "CSV")}>
        <Typography>エクスポート(CSV)</Typography>
      </MenuItem>
      <MenuItem component={Link} to={importEntriesPath(entityId)}>
        <Typography>インポート</Typography>
      </MenuItem>
      <MenuItem component={Link} to={entityHistoryPath(entityId)}>
        <Typography>変更履歴</Typography>
      </MenuItem>
      <Confirmable
        componentGenerator={(handleOpen) => (
          <MenuItem onClick={handleOpen}>
            <ListItemText>削除</ListItemText>
            <ListItemIcon>
              <DeleteOutlineIcon />
            </ListItemIcon>
          </MenuItem>
        )}
        dialogTitle="本当に削除しますか？"
        onClickYes={(e) => handleDelete(e, entityId)}
      />
    </Menu>
  );
};
