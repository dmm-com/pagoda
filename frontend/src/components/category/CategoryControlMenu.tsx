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
import { Link, useNavigate } from "react-router";

import { Confirmable } from "components/common/Confirmable";
import { useTranslation } from "hooks/useTranslation";
import { translate } from "i18n/config";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  aclPath,
  editCategoryPath,
  listCategoryPath,
  topPath,
} from "routes/Routes";
import { canEdit, canModifyACL } from "services/ACLUtil";

interface Props {
  categoryId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (categoryId: number) => void;
  setToggle?: () => void;
  permission?: number;
}

export const CategoryControlMenu: FC<Props> = ({
  categoryId,
  anchorElem,
  handleClose,
  setToggle,
  permission,
}) => {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleDelete = async (categoryId: number) => {
    await aironeApiClient
      .deleteCategory(categoryId)
      .then(() => {
        enqueueSnackbar(translate("category.menu.deleteSuccess"), {
          variant: "success",
        });
        // A magic to reload the category list with keeping snackbar
        navigate(topPath(), { replace: true });
        navigate(listCategoryPath(), { replace: true });
        setToggle && setToggle();
      })
      .catch(() => {
        enqueueSnackbar(translate("category.menu.deleteFailed"), {
          variant: "error",
        });
      });
  };

  return (
    <Menu
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
      {(permission === undefined || canEdit(permission)) && (
        <MenuItem component={Link} to={editCategoryPath(categoryId)}>
          <Typography>{t("common.edit")}</Typography>
        </MenuItem>
      )}
      {(permission === undefined || canModifyACL(permission)) && (
        <MenuItem component={Link} to={aclPath(categoryId)}>
          <Typography>{t("category.menu.acl")}</Typography>
        </MenuItem>
      )}
      {(permission === undefined || canModifyACL(permission)) && (
        <Confirmable
          componentGenerator={(handleOpen) => (
            <MenuItem onClick={handleOpen}>
              <ListItemText>{t("common.delete")}</ListItemText>
              <ListItemIcon>
                <DeleteOutlineIcon />
              </ListItemIcon>
            </MenuItem>
          )}
          dialogTitle={t("category.menu.confirmDelete")}
          onClickYes={() => handleDelete(categoryId)}
        />
      )}
    </Menu>
  );
};
