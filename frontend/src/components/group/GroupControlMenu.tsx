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
import React, { FC, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Confirmable } from "components/common/Confirmable";
import { aironeApiClient } from "repository/AironeApiClient";
import { groupPath, groupsPath, topPath } from "routes/Routes";

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
  const navigate = useNavigate();

  const handleDelete = useCallback(async () => {
    try {
      await aironeApiClient.deleteGroup(groupId);
      enqueueSnackbar(`グループの削除が完了しました`, {
        variant: "success",
      });
      navigate(topPath(), { replace: true });
      navigate(groupsPath(), { replace: true });
      setToggle && setToggle();
    } catch (e) {
      enqueueSnackbar("グループの削除が失敗しました", {
        variant: "error",
      });
    }
  }, [navigate, enqueueSnackbar, groupId]);

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
      <Box sx={{ width: 150 }}>
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
          dialogTitle={`本当に削除しますか？`}
          onClickYes={handleDelete}
        />
      </Box>
    </Menu>
  );
};
