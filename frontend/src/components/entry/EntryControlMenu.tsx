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
import { FC } from "react";
import { Link, useNavigate } from "react-router";

import { Confirmable } from "components/common/Confirmable";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  entryEditPath,
  aclPath,
  showEntryHistoryPath,
  copyEntryPath,
  entityEntriesPath,
  topPath,
  entryDetailsPath,
  aclHistoryPath,
} from "routes/Routes";
import { canEdit, canModifyACL } from "services/ACLUtil";

interface EntryControlProps {
  entityId: number;
  entryId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (entryId: number) => void;
  setToggle?: () => void;
  disableChangeHistory?: boolean;
  customDetailPath?: string;
  customEditPath?: string;
  customCopyPath?: string;
  customACLPath?: string;
  customHistoryPath?: string;
  customACLHistoryPath?: string;
  permission?: number;
  entityPermission?: number;
}

export const EntryControlMenu: FC<EntryControlProps> = ({
  entityId,
  entryId,
  anchorElem,
  handleClose,
  setToggle,
  disableChangeHistory = false,
  customDetailPath,
  customEditPath,
  customCopyPath,
  customACLPath,
  customHistoryPath,
  customACLHistoryPath,
  permission,
  entityPermission,
}) => {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleDelete = async (entryId: number) => {
    try {
      await aironeApiClient.destroyEntry(entryId);
      enqueueSnackbar(t("entry.control.deleteSuccess"), {
        variant: "success",
      });
      setToggle && setToggle();
      navigate(topPath(), { replace: true });
      navigate(entityEntriesPath(entityId), { replace: true });
    } catch (e) {
      enqueueSnackbar(t("entry.control.deleteFailure"), {
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
    >
      <Box sx={{ width: 150 }}>
        <MenuItem
          component={Link}
          to={
            customDetailPath
              ? customDetailPath
              : entryDetailsPath(entityId, entryId)
          }
        >
          <Typography>{t("common.details")}</Typography>
        </MenuItem>
        {(permission === undefined || canEdit(permission)) && (
          <MenuItem
            component={Link}
            to={
              customEditPath ? customEditPath : entryEditPath(entityId, entryId)
            }
          >
            <Typography>{t("common.edit")}</Typography>
          </MenuItem>
        )}
        {(entityPermission === undefined || canEdit(entityPermission)) && (
          <MenuItem
            component={Link}
            to={
              customCopyPath ? customCopyPath : copyEntryPath(entityId, entryId)
            }
          >
            <Typography>{t("common.copy")}</Typography>
          </MenuItem>
        )}
        {(permission === undefined || canModifyACL(permission)) && (
          <MenuItem
            component={Link}
            to={customACLPath ? customACLPath : aclPath(entryId)}
          >
            <Typography>{t("entry.control.aclSettings")}</Typography>
          </MenuItem>
        )}
        <MenuItem
          component={Link}
          to={
            customHistoryPath
              ? customHistoryPath
              : showEntryHistoryPath(entityId, entryId)
          }
          disabled={disableChangeHistory}
        >
          <Typography>{t("entry.common.changeHistory")}</Typography>
        </MenuItem>
        <MenuItem
          component={Link}
          to={
            customACLHistoryPath
              ? customACLHistoryPath
              : aclHistoryPath(entryId)
          }
        >
          <Typography>{t("entry.control.aclChangeHistory")}</Typography>
        </MenuItem>
        {(permission === undefined || canEdit(permission)) && (
          <Confirmable
            componentGenerator={(handleOpen) => (
              <MenuItem onClick={handleOpen} sx={{ justifyContent: "end" }}>
                <ListItemText>{t("common.delete")}</ListItemText>
                <ListItemIcon>
                  <DeleteOutlineIcon />
                </ListItemIcon>
              </MenuItem>
            )}
            dialogTitle={t("entry.control.confirmDelete")}
            onClickYes={() => handleDelete(entryId)}
          />
        )}
      </Box>
    </Menu>
  );
};
