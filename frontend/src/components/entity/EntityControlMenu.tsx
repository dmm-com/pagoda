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
import { Link, useHistory } from "react-router-dom";

import { RateLimitedClickable } from "../common/RateLimitedClickable";

import {
  aclPath,
  entityHistoryPath,
  entityPath,
  entitiesPath,
  restoreEntryPath,
  topPath,
  entityEntriesPath,
} from "Routes";
import { Confirmable } from "components/common/Confirmable";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

type ExportFormatType = "YAML" | "CSV";

interface Props {
  entityId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (entityId: number) => void;
  setOpenImportModal: (isOpened: boolean) => void;
}

export const EntityControlMenu: FC<Props> = ({
  entityId,
  anchorElem,
  handleClose,
  setOpenImportModal,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();

  const handleDelete = async (entityId: number) => {
    await aironeApiClientV2
      .deleteEntity(entityId)
      .then(() => {
        enqueueSnackbar("エンティティの削除が完了しました", {
          variant: "success",
        });
        // A magic to reload the entity list with keeping snackbar
        history.replace(topPath());
        history.replace(entitiesPath());
      })
      .catch(() => {
        enqueueSnackbar("エンティティの削除が失敗しました", {
          variant: "error",
        });
      });
  };
  const handleExport = async (entityId: number, format: ExportFormatType) => {
    try {
      await aironeApiClientV2.exportEntries(entityId, format);
      enqueueSnackbar("エンティティのエクスポートのジョブ登録が成功しました", {
        variant: "success",
      });
    } catch (e) {
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
      anchorOrigin={{
        vertical: "bottom",
        horizontal: "right",
      }}
      transformOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
      disableScrollLock
    >
      <MenuItem component={Link} to={entityEntriesPath(entityId)}>
        <Typography>エントリ一覧</Typography>
      </MenuItem>
      <MenuItem component={Link} to={entityPath(entityId)}>
        <Typography>編集</Typography>
      </MenuItem>
      <MenuItem component={Link} to={aclPath(entityId)}>
        <Typography>ACL 設定</Typography>
      </MenuItem>
      <MenuItem component={Link} to={entityHistoryPath(entityId)}>
        <Typography>変更履歴</Typography>
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
        <Typography>削除エントリの復旧</Typography>
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
