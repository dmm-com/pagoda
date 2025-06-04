import { UserList } from "@dmm-com/airone-apiclient-typescript-fetch";
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
import { useNavigate } from "react-router";

import { Confirmable } from "components/common/Confirmable";
import { aironeApiClient } from "repository/AironeApiClient";
import { topPath } from "routes/Routes";
import { usersPath } from "routes/Routes";

interface UserControlProps {
  user: UserList;
  anchorElem: HTMLButtonElement | null;
  handleClose: (userId: number) => void;
  onClickEditPassword: (userId: number) => void;
  setToggle?: () => void;
}

export const UserControlMenu: FC<UserControlProps> = ({
  user,
  anchorElem,
  handleClose,
  onClickEditPassword,
  setToggle,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleDelete = async (user: UserList) => {
    try {
      await aironeApiClient.destroyUser(user.id);
      enqueueSnackbar(`ユーザ(${user.username})の削除が完了しました`, {
        variant: "success",
      });
      navigate(topPath(), { replace: true });
      navigate(usersPath(), { replace: true });
      setToggle && setToggle();
    } catch (e) {
      enqueueSnackbar("ユーザの削除が失敗しました", {
        variant: "error",
      });
    }
  };

  return (
    <Menu
      id={`userControlMenu-${user.id}`}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(user.id)}
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
          onClick={() => {
            handleClose(user.id);
            onClickEditPassword(user.id);
          }}
        >
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
          dialogTitle={`本当に削除しますか？(${user.username})`}
          onClickYes={() => handleDelete(user)}
        />
      </Box>
    </Menu>
  );
};
