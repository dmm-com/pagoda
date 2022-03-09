import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  Box,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import React, { FC } from "react";
import { Link, useHistory } from "react-router-dom";

import {
  entryPath,
  aclPath,
  showEntryHistoryPath,
  copyEntryPath,
} from "Routes";
import { Confirmable } from "components/common/Confirmable";
import { deleteEntry } from "utils/AironeAPIClient";

interface EntryControlProps {
  entryId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (entryId: number) => void;
}

export const EntryControlMenu: FC<EntryControlProps> = ({
  entryId,
  anchorElem,
  handleClose,
}) => {
  const history = useHistory();

  const handleDelete = async (event, entryId) => {
    await deleteEntry(entryId);
    history.go(0);
  };

  return (
    <Menu
      id={`entityControlMenu-${entryId}`}
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
        <MenuItem component={Link} to={entryPath(entryId)}>
          <Typography>編集</Typography>
        </MenuItem>
        <MenuItem component={Link} to={copyEntryPath(entryId)}>
          <Typography>コピー</Typography>
        </MenuItem>
        <MenuItem component={Link} to={aclPath(entryId)}>
          <Typography>ACL 設定</Typography>
        </MenuItem>
        <MenuItem component={Link} to={showEntryHistoryPath(entryId)}>
          <Typography>変更履歴</Typography>
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
          onClickYes={(e) => handleDelete(e, entryId)}
        />
      </Box>
    </Menu>
  );
};
