import { Button } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC } from "react";

import { useTranslation } from "hooks/useTranslation";
import { NotificationMessages } from "services/NotificationMessages";

interface Props {
  onExport: () => Promise<void>;
}

const EXPORT_REQUEST_LOCK = "airone-export-request";
const EXPORT_REQUEST_STARTED_AT_KEY = "job__export_request_started_at";
const EXPORT_REQUEST_DEBOUNCE_MS = 15_000;

const registerExportOnce = async (
  onExport: () => Promise<void>,
  notifyRegistered: () => void,
): Promise<void> => {
  const now = Date.now();
  const lastRequest = Number(
    localStorage.getItem(EXPORT_REQUEST_STARTED_AT_KEY),
  );
  if (now - lastRequest < EXPORT_REQUEST_DEBOUNCE_MS) return;

  localStorage.setItem(EXPORT_REQUEST_STARTED_AT_KEY, String(now));
  try {
    await onExport();
  } catch (error) {
    if (localStorage.getItem(EXPORT_REQUEST_STARTED_AT_KEY) === String(now)) {
      localStorage.removeItem(EXPORT_REQUEST_STARTED_AT_KEY);
    }
    throw error;
  }
  notifyRegistered();
};

export const ExportButton: FC<Props> = ({ onExport }) => {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  const handleExport = async () => {
    const notifyRegistered = () =>
      enqueueSnackbar(NotificationMessages.jobRegistered(t("common.export")), {
        variant: "info",
      });

    try {
      if (navigator.locks) {
        await navigator.locks.request(
          EXPORT_REQUEST_LOCK,
          { ifAvailable: true },
          async (lock) => {
            if (lock) await registerExportOnce(onExport, notifyRegistered);
          },
        );
      } else {
        await registerExportOnce(onExport, notifyRegistered);
      }
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
