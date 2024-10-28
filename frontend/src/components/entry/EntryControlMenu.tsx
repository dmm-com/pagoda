import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  entryEditPath,
  aclPath,
  showEntryHistoryPath,
  copyEntryPath,
  entityEntriesPath,
  topPath,
  entryDetailsPath,
  aclHistoryPath,
} from "Routes";
import { Confirmable } from "components/common/Confirmable";
import { aironeApiClient } from "repository/AironeApiClient";

interface EntryControlProps {
  entityId: number;
  entryId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (entryId: number) => void;
  setToggle?: () => void;
  disableChangeHistory?: boolean;
  customDetailPath?: string;
  customEditPath?: string;
  customCopyPath?: string;
  customACLPath?: string;
  customHistoryPath?: string;
  customACLHistoryPath?: string;
}

export const EntryControlMenu: FC<EntryControlProps> = ({
  entityId,
  entryId,
  anchorElem,
  handleClose,
  setToggle,
  disableChangeHistory = false,
  customDetailPath,
  customEditPath,
  customCopyPath,
  customACLPath,
  customHistoryPath,
  customACLHistoryPath,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleDelete = async (entryId: number) => {
    try {
      await aironeApiClient.destroyEntry(entryId);
      enqueueSnackbar("アイテムの削除が完了しました", {
        variant: "success",
      });
      setToggle && setToggle();
      navigate(topPath(), { replace: true });
      navigate(entityEntriesPath(entityId), { replace: true });
    } catch (e) {
      enqueueSnackbar("アイテムの削除が失敗しました", {
        variant: "error",
      });
    }
  };

  return (
    <Menu
      id={`entryControlMenu-${entryId}`}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(entryId)}
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
      <Box sx={{ width: 150 }}>
        <MenuItem
          component={Link}
          to={
            customDetailPath
              ? customDetailPath
              : entryDetailsPath(entityId, entryId)
          }
        >
          <Typography>詳細</Typography>
        </MenuItem>
        <MenuItem
          component={Link}
          to={
            customEditPath ? customEditPath : entryEditPath(entityId, entryId)
          }
        >
          <Typography>編集</Typography>
        </MenuItem>
        <MenuItem
          component={Link}
          to={
            customCopyPath ? customCopyPath : copyEntryPath(entityId, entryId)
          }
        >
          <Typography>コピー</Typography>
        </MenuItem>
        <MenuItem
          component={Link}
          to={customACLPath ? customACLPath : aclPath(entryId)}
        >
          <Typography>ACL 設定</Typography>
        </MenuItem>
        <MenuItem
          component={Link}
          to={
            customHistoryPath
              ? customHistoryPath
              : showEntryHistoryPath(entityId, entryId)
          }
          disabled={disableChangeHistory}
        >
          <Typography>変更履歴</Typography>
        </MenuItem>
        <MenuItem
          component={Link}
          to={
            customACLHistoryPath
              ? customACLHistoryPath
              : aclHistoryPath(entryId)
          }
        >
          <Typography>ACL 変更履歴</Typography>
        </MenuItem>
        <Confirmable
          componentGenerator={(handleOpen) => (
            <MenuItem onClick={handleOpen} sx={{ justifyContent: "end" }}>
              <ListItemText>削除</ListItemText>
              <ListItemIcon>
                <DeleteOutlineIcon />
              </ListItemIcon>
            </MenuItem>
          )}
          dialogTitle="本当に削除しますか？"
          onClickYes={() => handleDelete(entryId)}
        />
      </Box>
    </Menu>
  );
};
