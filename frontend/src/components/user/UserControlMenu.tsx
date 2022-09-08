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

import { passwordPath } from "Routes";
import { Confirmable } from "components/common/Confirmable";

interface UserControlProps {
  userId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (userId: number) => void;
}

export const UserControlMenu: FC<UserControlProps> = ({
  userId,
  anchorElem,
  handleClose,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();

  const handleDelete = async (event, userId) => {
    // FIXME implement delete user API V2, then call it
    /*
    try {
      await aironeApiClientV2.destroyEntry(entryId);
      enqueueSnackbar("エントリの削除が完了しました", {
        variant: "success",
      });
      history.replace(topPath());
      history.replace(entityEntriesPath(entityId));
    } catch (e) {
      enqueueSnackbar("エントリの削除が失敗しました", {
        variant: "error",
      });
    }
     */
  };

  return (
    <Menu
      id={`userControlMenu-${userId}`}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(userId)}
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
        <MenuItem component={Link} to={passwordPath(userId)}>
          <Typography>パスワード編集</Typography>
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
          onClickYes={(e) => handleDelete(e, userId)}
        />
      </Box>
    </Menu>
  );
};
