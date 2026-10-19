import { JobSerializers } from "@dmm-com/airone-apiclient-typescript-fetch";
import CloseIcon from "@mui/icons-material/Close";
import { Button, IconButton } from "@mui/material";
import { SnackbarKey, useSnackbar } from "notistack";
import { useEffect, useRef } from "react";

import { translate } from "../i18n/config";
import {
  LocalStorageKey,
  localStorageUtil,
} from "../repository/LocalStorageUtil";

import { jobsPath } from "routes/Routes";
import { JobStatuses } from "services/Constants";
import { isExportJob, jobOperationLabel } from "services/JobUtil";
import { NotificationMessages } from "services/NotificationMessages";

const NOTIFICATION_AUTO_HIDE_DURATION_MS = 8000;

const isTerminalStatus = (status: number | undefined): boolean =>
  status === JobStatuses.DONE ||
  status === JobStatuses.ERROR ||
  status === JobStatuses.TIMEOUT;

const loadNotifiedIds = (): Set<number> => {
  const raw = localStorageUtil.get(LocalStorageKey.JobNotifiedIds);
  if (raw == null) return new Set();
  try {
    return new Set(JSON.parse(raw) as number[]);
  } catch {
    return new Set();
  }
};

const saveNotifiedIds = (ids: Set<number>) => {
  localStorageUtil.set(
    LocalStorageKey.JobNotifiedIds,
    JSON.stringify([...ids]),
  );
};

export const useJobCompletionNotification = (
  recentJobs: JobSerializers[],
): void => {
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const notifiedIdsRef = useRef<Set<number>>(loadNotifiedIds());
  const isFirstLoadRef = useRef(true);
  const mountedAtRef = useRef(new Date());

  useEffect(() => {
    if (recentJobs.length === 0) return;

    // Ignore historical completions, including after remounting the header.
    if (isFirstLoadRef.current) {
      isFirstLoadRef.current = false;
      for (const job of recentJobs) {
        if (
          isTerminalStatus(job.status) &&
          job.createdAt <= mountedAtRef.current
        ) {
          notifiedIdsRef.current.add(job.id);
        }
      }
      saveNotifiedIds(notifiedIdsRef.current);
    }

    const newlyNotified: number[] = [];

    for (const job of recentJobs) {
      if (!isTerminalStatus(job.status)) continue;
      if (notifiedIdsRef.current.has(job.id)) continue;

      const targetName =
        job.target?.name ??
        (isExportJob(job.operation)
          ? job.text
          : jobOperationLabel(job.operation));

      const closeAction = (snackbarId: SnackbarKey) => (
        <IconButton
          size="small"
          color="inherit"
          onClick={() => closeSnackbar(snackbarId)}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      );

      if (job.status === JobStatuses.DONE) {
        if (isExportJob(job.operation)) {
          const link = document.createElement("a");
          link.href = `/job/api/v2/${job.id}/download?encode=utf-8`;
          link.download = "";
          document.body.appendChild(link);
          link.click();
          link.remove();
          enqueueSnackbar(NotificationMessages.exportReady(targetName), {
            variant: "success",
            persist: true,
            action: (snackbarId) => (
              <>
                <Button
                  size="small"
                  color="inherit"
                  href={`/job/api/v2/${job.id}/download?encode=utf-8`}
                  onClick={() => closeSnackbar(snackbarId)}
                >
                  {translate("common.download")}
                </Button>
                {closeAction(snackbarId)}
              </>
            ),
          });
        } else {
          enqueueSnackbar(NotificationMessages.jobCompleted(targetName), {
            variant: "success",
            autoHideDuration: NOTIFICATION_AUTO_HIDE_DURATION_MS,
            action: (snackbarId) => (
              <>
                <Button
                  size="small"
                  color="inherit"
                  href={jobsPath()}
                  onClick={() => closeSnackbar(snackbarId)}
                >
                  {translate("common.details")}
                </Button>
                {closeAction(snackbarId)}
              </>
            ),
          });
        }
      } else if (job.status === JobStatuses.ERROR) {
        enqueueSnackbar(NotificationMessages.jobFailed(targetName), {
          variant: "error",
          persist: true,
          action: (snackbarId) => (
            <>
              <Button
                size="small"
                color="inherit"
                href={jobsPath()}
                onClick={() => closeSnackbar(snackbarId)}
              >
                {translate("common.details")}
              </Button>
              {closeAction(snackbarId)}
            </>
          ),
        });
      } else if (job.status === JobStatuses.TIMEOUT) {
        enqueueSnackbar(NotificationMessages.jobTimedOut(targetName), {
          variant: "warning",
          autoHideDuration: NOTIFICATION_AUTO_HIDE_DURATION_MS,
          action: (snackbarId) => (
            <>
              <Button
                size="small"
                color="inherit"
                href={jobsPath()}
                onClick={() => closeSnackbar(snackbarId)}
              >
                {translate("common.details")}
              </Button>
              {closeAction(snackbarId)}
            </>
          ),
        });
      }

      newlyNotified.push(job.id);
    }

    if (newlyNotified.length > 0) {
      for (const id of newlyNotified) {
        notifiedIdsRef.current.add(id);
      }

      // Prune IDs no longer in recentJobs
      const currentJobIds = new Set(recentJobs.map((j) => j.id));
      for (const id of notifiedIdsRef.current) {
        if (!currentJobIds.has(id)) {
          notifiedIdsRef.current.delete(id);
        }
      }

      saveNotifiedIds(notifiedIdsRef.current);
    }
  }, [recentJobs, enqueueSnackbar, closeSnackbar]);
};
