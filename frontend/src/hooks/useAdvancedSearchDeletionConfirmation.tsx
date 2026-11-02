import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import { useEffect, useRef, useState } from "react";

import {
  AdvancedSearchTarget,
  AdvancedSearchTargetList,
} from "components/entry/AdvancedSearchTargetList";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { EntryReferralList } from "services/Constants";

type DeleteTarget = AdvancedSearchTarget & {
  referrals: NonNullable<AdvancedSearchTarget["referrals"]>;
};

const PAGE_SIZE = 10;

export const useAdvancedSearchDeletionConfirmation = () => {
  const { t } = useTranslation();
  const [state, setState] = useState<{
    status: "checking" | "ready" | "error";
    targets: DeleteTarget[];
    page: number;
  } | null>(null);
  const pending = useRef<((confirmed: boolean) => void) | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

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

  const confirmDeletion = async (
    entryIds: number[],
    entryNames: Record<number, string>,
  ): Promise<boolean> => {
    if (pending.current || entryIds.length === 0) return false;
    const decision = new Promise<boolean>((resolve) => {
      pending.current = resolve;
    });
    const request = pending.current;
    const ids = [...new Set(entryIds)];
    setState({
      status: "checking",
      targets: ids.map((id) => ({
        id,
        name: entryNames[id] ?? `#${id}`,
        referrals: [],
      })),
      page: 1,
    });
    try {
      const targets: DeleteTarget[] = new Array(ids.length);
      let nextIndex = 0;
      await Promise.all(
        Array.from({ length: Math.min(8, ids.length) }, async () => {
          while (nextIndex < ids.length && pending.current === request) {
            const index = nextIndex++;
            const id = ids[index]!;
            const first = await aironeApiClient.getEntryReferral(id, 1);
            const referrals = [...first.results];
            const pageCount = Math.ceil(
              first.count / EntryReferralList.MAX_ROW_COUNT,
            );
            for (
              let page = 2;
              page <= pageCount && pending.current === request;
              page++
            ) {
              const response = await aironeApiClient.getEntryReferral(id, page);
              referrals.push(...response.results);
            }
            const name =
              entryNames[id] ?? (await aironeApiClient.getEntry(id)).name;
            targets[index] = {
              id,
              name,
              referrals: referrals.filter((entry) => entry.id !== id),
            };
          }
        }),
      );
      if (pending.current === request) {
        setState({ status: "ready", targets, page: 1 });
      }
    } catch {
      if (pending.current === request) {
        setState((previous) => previous && { ...previous, status: "error" });
      }
    }
    return decision;
  };

  const page = state?.page ?? 1;
  const targets = state?.targets ?? [];
  const hasReferrals = targets.some((target) => target.referrals.length > 0);
  const deletionConfirmationDialog = (
    <Dialog
      open={state !== null}
      onClose={() => finish(false)}
      aria-labelledby="advanced-search-delete-title"
      maxWidth="md"
      fullWidth
    >
      <DialogTitle id="advanced-search-delete-title">
        {t("advancedSearch.resultsPage.deleteDialogTitle", {
          count: targets.length,
        })}
      </DialogTitle>
      <DialogContent dividers ref={contentRef}>
        {state?.status === "checking" && (
          <Typography>{t("entry.control.checkingReferences")}</Typography>
        )}
        {state?.status === "error" && (
          <Alert severity="error">
            {t("entry.control.referenceCheckFailure")}
          </Alert>
        )}
        {state?.status === "ready" && (
          <>
            {hasReferrals && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {t("advancedSearch.resultsPage.deleteReferenceWarning")}
              </Alert>
            )}
            <AdvancedSearchTargetList
              targets={targets.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)}
              totalCount={targets.length}
              page={page}
              onPageChange={(nextPage) => {
                setState(
                  (previous) => previous && { ...previous, page: nextPage },
                );
                contentRef.current?.scrollTo?.({ top: 0 });
              }}
            />
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => finish(false)}>{t("common.cancel")}</Button>
        <Button
          color="error"
          disabled={state?.status !== "ready"}
          onClick={() => finish(true)}
        >
          {hasReferrals
            ? t("entry.control.deleteAnyway")
            : t("advancedSearch.resultsPage.confirmDeleteAction")}
        </Button>
      </DialogActions>
    </Dialog>
  );

  return { confirmDeletion, deletionConfirmationDialog };
};
