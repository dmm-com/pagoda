import { UserList } from "@dmm-com/airone-apiclient-typescript-fetch";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { FC } from "react";

import { Confirmable } from "components/common/Confirmable";
import { aironeApiClient } from "repository/AironeApiClient";

interface UserControlProps {
  user: UserList;
  anchorElem: HTMLButtonElement | null;
  handleClose: (userId: number) => void;
  onClickEditPassword: (userId: number) => void;
  setToggle?: () => void;
  isSelf?: boolean;
  isCoUser?: boolean;
}

export const UserControlMenu: FC<UserControlProps> = ({
  user,
  anchorElem,
  handleClose,
  onClickEditPassword,
  setToggle,
  isSelf = false,
  isCoUser = false,
}) => {
  const { enqueueSnackbar } = useSnackbar();

  const handleDelete = async (user: UserList) => {
    try {
      await aironeApiClient.destroyUser(user.id);
      handleClose(user.id);
      enqueueSnackbar(`ユーザ(${user.username})の削除が完了しました`, {
        variant: "success",
      });
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
      {[
        <MenuItem
          key="password"
          onClick={() => {
            handleClose(user.id);
            onClickEditPassword(user.id);
          }}
        >
          <Typography>パスワード編集</Typography>
        </MenuItem>,
        (!isSelf || isCoUser) && (
          <Confirmable
            key="delete"
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
        ),
      ]}
    </Menu>
  );
};
