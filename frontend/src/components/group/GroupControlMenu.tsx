import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, useCallback } from "react";
import { Link } from "react-router";

import { Confirmable } from "components/common/Confirmable";
import { aironeApiClient } from "repository/AironeApiClient";
import { groupPath } from "routes/Routes";

interface Props {
  groupId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
  setToggle?: () => void;
}

export const GroupControlMenu: FC<Props> = ({
  groupId,
  anchorElem,
  handleClose,
  setToggle,
}) => {
  const { enqueueSnackbar } = useSnackbar();

  const handleDelete = useCallback(async () => {
    try {
      await aironeApiClient.deleteGroup(groupId);
      handleClose();
      enqueueSnackbar(`グループの削除が完了しました`, {
        variant: "success",
      });
      setToggle && setToggle();
    } catch (e) {
      enqueueSnackbar("グループの削除が失敗しました", {
        variant: "error",
      });
    }
  }, [enqueueSnackbar, groupId, handleClose, setToggle]);

  return (
    <Menu
      open={Boolean(anchorElem)}
      onClose={handleClose}
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
      <MenuItem component={Link} to={groupPath(groupId)}>
        <Typography>グループ編集</Typography>
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
        onClickYes={handleDelete}
      />
    </Menu>
  );
};
