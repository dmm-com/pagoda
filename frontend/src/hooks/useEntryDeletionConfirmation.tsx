import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Link,
  Typography,
} from "@mui/material";
import { useEffect, useRef, useState } from "react";

import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { entryDetailsPath } from "routes/Routes";

type Referral = Pick<EntryBase, "id" | "name" | "schema">;
type CheckResult = {
  entryId: number;
  entryName?: string;
  count: number;
  referrals: Referral[];
};

export const useEntryDeletionConfirmation = () => {
  const { t } = useTranslation();
  const [state, setState] = useState<{
    status: "checking" | "warning" | "error" | "confirm";
    confirmationTitle?: string;
    results: CheckResult[];
  } | null>(null);
  const pending = useRef<((confirmed: boolean) => void) | null>(null);

  useEffect(
    () => () => {
      pending.current?.(false);
      pending.current = null;
    },
    [],
  );

  const finish = (confirmed: boolean) => {
    const resolve = pending.current;
    pending.current = null;
    setState(null);
    resolve?.(confirmed);
  };

  const confirmEntryDeletion = async (
    entryIds: number[],
    confirmationTitle?: string,
    entryNames: Record<number, string> = {},
  ): Promise<boolean> => {
    if (pending.current) return false;
    if (entryIds.length === 0) return true;
    const decision = new Promise<boolean>((resolve) => {
      pending.current = resolve;
    });
    const request = pending.current;
    setState({ status: "checking", results: [] });
    try {
      const results: CheckResult[] = [];
      for (const entryId of new Set(entryIds)) {
        if (pending.current !== request) return decision;
        const response = await aironeApiClient.getEntryReferral(entryId, 1);
        const referrals = response.results.filter(
          (entry) => entry.id !== entryId,
        );
        const count =
          (response.count ?? response.results.length) -
          (response.results.some((entry) => entry.id === entryId) ? 1 : 0);
        if (count > 0)
          results.push({
            entryId,
            entryName: entryNames[entryId],
            count,
            referrals,
          });
      }
      if (pending.current === request) {
        if (results.length > 0) setState({ status: "warning", results });
        else if (confirmationTitle)
          setState({ status: "confirm", results: [], confirmationTitle });
        else finish(true);
      }
    } catch {
      if (pending.current === request)
        setState({ status: "error", results: [] });
    }
    return decision;
  };

  const deletionConfirmationDialog = (
    <Dialog
      open={state !== null}
      onClose={() => finish(false)}
      aria-labelledby="entry-deletion-warning-title"
    >
      <DialogTitle id="entry-deletion-warning-title">
        {state?.status === "confirm"
          ? state.confirmationTitle
          : state?.status === "checking"
            ? t("entry.control.checkingReferences")
            : t("entry.control.referenceWarningTitle")}
      </DialogTitle>
      <DialogContent>
        {state?.status === "checking" && (
          <Typography>{t("entry.control.checkingReferences")}</Typography>
        )}
        {state?.status === "error" && (
          <Alert severity="error">
            {t("entry.control.referenceCheckFailure")}
          </Alert>
        )}
        {state?.status === "warning" && (
          <>
            <Alert severity="warning">
              {t("entry.control.referenceWarning")}
            </Alert>
            {state.results.map(({ entryId, entryName, count, referrals }) => (
              <div key={entryId}>
                <Typography sx={{ mt: 2 }}>
                  {entryName || `#${entryId}`}:{" "}
                  {t("entry.control.referenceCount", { count })}
                </Typography>
                <ul>
                  {referrals.map((entry) => (
                    <li key={entry.id}>
                      <Link
                        href={entryDetailsPath(entry.schema.id, entry.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {entry.schema.name} / {entry.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button autoFocus onClick={() => finish(false)}>
          {state?.status === "confirm" ? "No" : t("common.cancel")}
        </Button>
        {state?.status === "confirm" && (
          <Button onClick={() => finish(true)}>Yes</Button>
        )}
        {state?.status === "warning" && (
          <Button color="error" onClick={() => finish(true)}>
            {t("entry.control.deleteAnyway")}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );

  return { confirmEntryDeletion, deletionConfirmationDialog };
};
