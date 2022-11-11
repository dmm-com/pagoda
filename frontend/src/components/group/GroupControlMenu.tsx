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
import { useHistory } from "react-router-dom";

import { groupPath, groupsPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { Confirmable } from "components/common/Confirmable";

interface Props {
  groupId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
}

export const GroupControlMenu: FC<Props> = ({
  groupId,
  anchorElem,
  handleClose,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const history = useHistory();

  const handleEdit = useCallback(() => {
    history.push(groupPath(groupId));
  }, [history, groupId]);

  const handleDelete = useCallback(async () => {
    try {
      await aironeApiClientV2.deleteGroup(groupId);
      enqueueSnackbar(`グループの削除が完了しました`, {
        variant: "success",
      });
      history.replace(topPath());
      history.replace(groupsPath());
    } catch (e) {
      enqueueSnackbar("グループの削除が失敗しました", {
        variant: "error",
      });
    }
  }, [history, enqueueSnackbar, groupId]);

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
      disableScrollLock
    >
      <Box sx={{ width: 150 }}>
        <MenuItem onClick={handleEdit}>
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
