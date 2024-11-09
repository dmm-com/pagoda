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
import { Link, useNavigate } from "react-router-dom";

import { RateLimitedClickable } from "../common/RateLimitedClickable";

import { Confirmable } from "components/common/Confirmable";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  aclPath,
  entityHistoryPath,
  editEntityPath,
  entitiesPath,
  restoreEntryPath,
  topPath,
  entityEntriesPath,
  aclHistoryPath,
} from "routes/Routes";

type ExportFormatType = "YAML" | "CSV";

interface Props {
  entityId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (entityId: number) => void;
  setOpenImportModal: (isOpened: boolean) => void;
  setToggle?: () => void;
}

export const EntityControlMenu: FC<Props> = ({
  entityId,
  anchorElem,
  handleClose,
  setOpenImportModal,
  setToggle,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleDelete = async (entityId: number) => {
    await aironeApiClient
      .deleteEntity(entityId)
      .then(() => {
        enqueueSnackbar("モデルの削除が完了しました", {
          variant: "success",
        });
        // A magic to reload the entity list with keeping snackbar
        navigate(topPath(), { replace: true });
        navigate(entitiesPath(), { replace: true });
        setToggle && setToggle();
      })
      .catch(() => {
        enqueueSnackbar("モデルの削除が失敗しました", {
          variant: "error",
        });
      });
  };
  const handleExport = async (entityId: number, format: ExportFormatType) => {
    try {
      await aironeApiClient.exportEntries(entityId, format);
      enqueueSnackbar("モデルのエクスポートのジョブ登録が成功しました", {
        variant: "success",
      });
    } catch (e) {
      enqueueSnackbar("モデルのエクスポートのジョブ登録が失敗しました", {
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
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      transformOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
    >
      <MenuItem component={Link} to={entityEntriesPath(entityId)}>
        <Typography>アイテム一覧</Typography>
      </MenuItem>
      <MenuItem component={Link} to={editEntityPath(entityId)}>
        <Typography>編集</Typography>
      </MenuItem>
      <MenuItem component={Link} to={aclPath(entityId)}>
        <Typography>ACL 設定</Typography>
      </MenuItem>
      <MenuItem component={Link} to={entityHistoryPath(entityId)}>
        <Typography>変更履歴</Typography>
      </MenuItem>
      <MenuItem component={Link} to={aclHistoryPath(entityId)}>
        <Typography>ACL 変更履歴</Typography>
      </MenuItem>
      <RateLimitedClickable
        intervalSec={5}
        onClick={handleExport.bind(null, entityId, "YAML")}
      >
        <MenuItem>
          <Typography>エクスポート(YAML)</Typography>
        </MenuItem>
      </RateLimitedClickable>
      <RateLimitedClickable
        intervalSec={5}
        onClick={handleExport.bind(null, entityId, "CSV")}
      >
        <MenuItem>
          <Typography>エクスポート(CSV)</Typography>
        </MenuItem>
      </RateLimitedClickable>
      <MenuItem onClick={() => setOpenImportModal(true)}>
        <Typography>インポート</Typography>
      </MenuItem>
      <MenuItem component={Link} to={restoreEntryPath(entityId)}>
        <Typography>削除アイテムの復旧</Typography>
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
        onClickYes={() => handleDelete(entityId)}
      />
    </Menu>
  );
};
