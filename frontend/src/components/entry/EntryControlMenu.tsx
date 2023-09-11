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
import { Link, useHistory } from "react-router-dom";

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
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

interface EntryControlProps {
  entityId: number;
  entryId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (entryId: number) => void;
  setToggle?: () => void;
}

export const EntryControlMenu: FC<EntryControlProps> = ({
  entityId,
  entryId,
  anchorElem,
  handleClose,
  setToggle,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();

  const handleDelete = async (entryId: number) => {
    try {
      await aironeApiClientV2.destroyEntry(entryId);
      enqueueSnackbar("エントリの削除が完了しました", {
        variant: "success",
      });
      setToggle && setToggle();
      history.replace(topPath());
      history.replace(entityEntriesPath(entityId));
    } catch (e) {
      enqueueSnackbar("エントリの削除が失敗しました", {
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
      disableScrollLock
    >
      <Box sx={{ width: 150 }}>
        <MenuItem component={Link} to={entryDetailsPath(entityId, entryId)}>
          <Typography>詳細</Typography>
        </MenuItem>
        <MenuItem component={Link} to={entryEditPath(entityId, entryId)}>
          <Typography>編集</Typography>
        </MenuItem>
        <MenuItem component={Link} to={copyEntryPath(entityId, entryId)}>
          <Typography>コピー</Typography>
        </MenuItem>
        <MenuItem component={Link} to={aclPath(entryId)}>
          <Typography>ACL 設定</Typography>
        </MenuItem>
        <MenuItem component={Link} to={showEntryHistoryPath(entityId, entryId)}>
          <Typography>変更履歴</Typography>
        </MenuItem>
        <MenuItem component={Link} to={aclHistoryPath(entryId)}>
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
