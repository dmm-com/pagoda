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
import { Link, useNavigate } from "react-router-dom";

import { Confirmable } from "components/common/Confirmable";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  aclPath,
  editCategoryPath,
  topPath,
  listCategoryPath,
} from "routes/Routes";

type ExportFormatType = "YAML" | "CSV";

interface Props {
  categoryId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (categoryId: number) => void;
  setOpenImportModal: (isOpened: boolean) => void;
  setToggle?: () => void;
}

export const CategoryControlMenu: FC<Props> = ({
  categoryId,
  anchorElem,
  handleClose,
  setOpenImportModal,
  setToggle,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleDelete = async (categoryId: number) => {
    console.log("[onix/handleDelete(00)] categoryId:", categoryId);
    await aironeApiClient
      .deleteCategory(categoryId)
      .then(() => {
        enqueueSnackbar("カテゴリの削除が完了しました", {
          variant: "success",
        });
        // A magic to reload the category list with keeping snackbar
        navigate(topPath(), { replace: true });
        navigate(listCategoryPath(), { replace: true });
        setToggle && setToggle();
      })
      .catch(() => {
        enqueueSnackbar("カテゴリの削除が失敗しました", {
          variant: "error",
        });
      });
  };

  return (
    <Menu
      id={`entityControlMenu-${categoryId}`}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(categoryId)}
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
      <MenuItem component={Link} to={editCategoryPath(categoryId)}>
        <Typography>編集</Typography>
      </MenuItem>
      <MenuItem component={Link} to={aclPath(categoryId)}>
        <Typography>ACL 設定</Typography>
      </MenuItem>
      {/*
      <MenuItem component={Link} to={aclHistoryPath(categoryId)}>
        <Typography>ACL 変更履歴</Typography>
      </MenuItem>
      */}
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
        onClickYes={() => handleDelete(categoryId)}
      />
    </Menu>
  );
};
