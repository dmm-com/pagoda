import { Box, Container } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, Suspense, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { preload } from "swr";

import { usePagodaSWR, wrapFetcher } from "../hooks/usePagodaSWR";
import { useTypedParams } from "../hooks/useTypedParams";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import {
  CopyFormProps,
  CopyForm as DefaultCopyForm,
} from "components/entry/CopyForm";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { usePrompt } from "hooks/usePrompt";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { entityEntriesPath, entryDetailsPath } from "routes/Routes";
import { NotificationMessages } from "services/NotificationMessages";

interface Props {
  CopyForm?: FC<CopyFormProps>;
}

const EntryCopyContent: FC<Props> = ({ CopyForm = DefaultCopyForm }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { entityId, entryId } = useTypedParams<{
    entityId: number;
    entryId: number;
  }>();

  // newline delimited string value, not string[]
  const [entries, _setEntries] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [edited, setEdited] = useState<boolean>(false);

  usePrompt(edited && !submitted, t("entryForm.editPage.leaveConfirm"));

  useEffect(() => {
    if (submitted) {
      navigate(entityEntriesPath(entityId), { replace: true });
    }
  }, [submitted, entityId, navigate]);

  const { data: entity } = usePagodaSWR(
    ["entity", entityId],
    () => aironeApiClient.getEntity(entityId),
    { suspense: true },
  );

  const { data: entry } = usePagodaSWR(
    ["entry", entryId],
    () => aironeApiClient.getEntry(entryId),
    { suspense: true },
  );

  const setEntries = (entries: string) => {
    setEdited(true);
    _setEntries(entries);
  };

  const handleCopy = async () => {
    setSubmitting(true);
    try {
      await aironeApiClient.copyEntry(
        entryId,
        entries
          .split("\n")
          .map((e) => e.trim())
          .filter((e) => e.length > 0),
      );

      setEdited(false);
      setSubmitted(true);
      enqueueSnackbar(NotificationMessages.jobRegistered(t("common.copy")), {
        variant: "info",
      });
    } catch {
      enqueueSnackbar(
        NotificationMessages.jobRegistrationFailed(t("common.copy")),
        {
          variant: "error",
        },
      );
    }
  };

  const handleCancel = () => {
    navigate(entryDetailsPath(entry.schema?.id ?? 0, entry.id), {
      replace: true,
    });
  };

  return (
    <>
      <EntryBreadcrumbs entry={entry} title={t("common.copy")} />

      <PageHeader
        title={entry.name ?? ""}
        description={t("entryForm.copyPage.description")}
      >
        <SubmitButton
          name={t("entryForm.copyPage.submitName")}
          disabled={!entries || submitting || submitted}
          isSubmitting={submitting}
          handleSubmit={handleCopy}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <Container>
        {entity.itemNameType == "US" ? (
          <CopyForm
            entries={entries}
            setEntries={setEntries}
            templateEntry={entry}
          />
        ) : (
          <Box>{t("entryForm.copyPage.cannotCopy")}</Box>
        )}
      </Container>
    </>
  );
};

export const EntryCopyPage: FC<Props> = ({ CopyForm = DefaultCopyForm }) => {
  const { entityId, entryId } = useTypedParams<{
    entityId: number;
    entryId: number;
  }>();

  preload(
    ["entity", entityId],
    wrapFetcher(() => aironeApiClient.getEntity(entityId)),
  );
  preload(
    ["entry", entryId],
    wrapFetcher(() => aironeApiClient.getEntry(entryId)),
  );

  return (
    <Box>
      <Suspense fallback={<Loading />}>
        <EntryCopyContent CopyForm={CopyForm} />
      </Suspense>
    </Box>
  );
};
