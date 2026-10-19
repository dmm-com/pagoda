import { Button } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC } from "react";

import { useTranslation } from "hooks/useTranslation";
import { NotificationMessages } from "services/NotificationMessages";

interface Props {
  onExport: () => Promise<void>;
}

export const ExportButton: FC<Props> = ({ onExport }) => {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  const handleExport = async () => {
    try {
      await onExport();
      enqueueSnackbar(NotificationMessages.jobRegistered(t("common.export")), {
        variant: "info",
      });
    } catch {
      enqueueSnackbar(
        NotificationMessages.jobRegistrationFailed(t("common.export")),
        { variant: "error" },
      );
    }
  };

  return (
    <Button
      variant="contained"
      color="info"
      sx={{ margin: "0 4px" }}
      onClick={handleExport}
    >
      {t("common.export")}
    </Button>
  );
};
