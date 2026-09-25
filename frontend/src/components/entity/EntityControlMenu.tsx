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

import { RateLimitedClickable } from "../common/RateLimitedClickable";

import { Confirmable } from "components/common/Confirmable";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  aclPath,
  entityHistoryPath,
  editEntityPath,
  entitiesPath,
  restoreEntryPath,
  listAliasPath,
  topPath,
  entityEntriesPath,
  aclHistoryPath,
} from "routes/Routes";
import { canEdit, canModifyACL } from "services/ACLUtil";
import {
  isResponseError,
  toReportableNonFieldErrors,
} from "services/AironeAPIErrorUtil";
import { NotificationMessages } from "services/NotificationMessages";

type ExportFormatType = "YAML" | "CSV";

interface Props {
  entityId: number;
  anchorElem: HTMLButtonElement | null;
  handleClose: (entityId: number) => void;
  setOpenImportModal: (isOpened: boolean) => void;
  setToggle?: () => void;
  permission?: number;
}

export const EntityControlMenu: FC<Props> = ({
  entityId,
  anchorElem,
  handleClose,
  setOpenImportModal,
  setToggle,
  permission,
}) => {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const handleDelete = async (entityId: number) => {
    try {
      await aironeApiClient.deleteEntity(entityId);
      enqueueSnackbar(t("entity.controlMenu.deleteSucceeded"), {
        variant: "success",
      });
      // A magic to reload the entity list with keeping snackbar
      navigate(topPath(), { replace: true });
      navigate(entitiesPath(), { replace: true });
      setToggle && setToggle();
    } catch (e) {
      const detail =
        e instanceof Error && isResponseError(e)
          ? await toReportableNonFieldErrors(e).catch((parseErr) => {
              console.error(
                "Failed to extract error detail from delete response",
                parseErr,
              );
              return null;
            })
          : null;
      enqueueSnackbar(
        detail
          ? t("entity.controlMenu.deleteFailedWithDetail", { detail })
          : t("entity.controlMenu.deleteFailed"),
        {
          variant: "error",
        },
      );
    }
  };
  const handleExport = async (entityId: number, format: ExportFormatType) => {
    try {
      await aironeApiClient.exportEntries(entityId, format);
      enqueueSnackbar(NotificationMessages.jobRegistered(t("common.export")), {
        variant: "info",
      });
    } catch (e) {
      enqueueSnackbar(
        NotificationMessages.jobRegistrationFailed(t("common.export")),
        {
          variant: "error",
        },
      );
    }
  };

  return (
    <Menu
      id={`entityControlMenu-${entityId}`}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(entityId)}
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
      <MenuItem component={Link} to={entityEntriesPath(entityId)}>
        <Typography>{t("entity.controlMenu.entryList")}</Typography>
      </MenuItem>
      <MenuItem component={Link} to={listAliasPath(entityId)}>
        <Typography>{t("entity.controlMenu.aliasList")}</Typography>
      </MenuItem>
      {(permission === undefined || canEdit(permission)) && (
        <MenuItem component={Link} to={editEntityPath(entityId)}>
          <Typography>{t("common.edit")}</Typography>
        </MenuItem>
      )}
      {(permission === undefined || canModifyACL(permission)) && (
        <MenuItem component={Link} to={aclPath(entityId)}>
          <Typography>{t("entity.controlMenu.aclSettings")}</Typography>
        </MenuItem>
      )}
      <MenuItem component={Link} to={entityHistoryPath(entityId)}>
        <Typography>{t("entity.controlMenu.history")}</Typography>
      </MenuItem>
      <MenuItem component={Link} to={aclHistoryPath(entityId)}>
        <Typography>{t("entity.controlMenu.aclHistory")}</Typography>
      </MenuItem>
      <RateLimitedClickable
        intervalSec={5}
        onClick={handleExport.bind(null, entityId, "YAML")}
      >
        <MenuItem>
          <Typography>
            {t("entity.controlMenu.exportFormat", { format: "YAML" })}
          </Typography>
        </MenuItem>
      </RateLimitedClickable>
      <RateLimitedClickable
        intervalSec={5}
        onClick={handleExport.bind(null, entityId, "CSV")}
      >
        <MenuItem>
          <Typography>
            {t("entity.controlMenu.exportFormat", { format: "CSV" })}
          </Typography>
        </MenuItem>
      </RateLimitedClickable>
      {(permission === undefined || canEdit(permission)) && (
        <MenuItem onClick={() => setOpenImportModal(true)}>
          <Typography>{t("common.import")}</Typography>
        </MenuItem>
      )}
      <MenuItem component={Link} to={restoreEntryPath(entityId)}>
        <Typography>{t("entity.controlMenu.restoreEntries")}</Typography>
      </MenuItem>
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
          dialogTitle={t("entity.controlMenu.deleteConfirm")}
          onClickYes={() => handleDelete(entityId)}
        />
      )}
    </Menu>
  );
};
