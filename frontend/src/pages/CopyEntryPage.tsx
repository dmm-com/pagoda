import { Box, Container } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { Prompt, useHistory } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import { entityEntriesPath, entryDetailsPath } from "Routes";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import {
  CopyForm as DefaultCopyForm,
  CopyFormProps,
} from "components/entry/CopyForm";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { aironeApiClient } from "repository/AironeApiClient";

interface Props {
  CopyForm?: FC<CopyFormProps>;
}

export const CopyEntryPage: FC<Props> = ({ CopyForm = DefaultCopyForm }) => {
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();

  // newline delimited string value, not string[]
  const [entries, _setEntries] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [edited, setEdited] = useState<boolean>(false);

  const entry = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntry(entryId);
  }, [entryId]);

  if (entry.loading) {
    return <Loading />;
  }

  const setEntries = (entries: string) => {
    setEdited(true);
    _setEntries(entries);
  };

  const handleCopy = async () => {
    setSubmitting(true);
    try {
      await aironeApiClient.copyEntry(entryId, entries.split("\n"));
      setSubmitted(true);
      enqueueSnackbar("エントリコピーのジョブ登録が成功しました", {
        variant: "success",
      });
      setTimeout(() => {
        history.replace(entityEntriesPath(entityId));
      }, 0.1);
    } catch {
      enqueueSnackbar("エントリコピーのジョブ登録が失敗しました", {
        variant: "error",
      });
    }
  };

  const handleCancel = () => {
    history.replace(
      entryDetailsPath(entry.value?.schema?.id ?? 0, entry.value?.id ?? 0)
    );
  };

  return (
    <Box>
      <EntryBreadcrumbs entry={entry.value} title="コピー" />

      <PageHeader
        title={entry.value?.name ?? ""}
        description="エントリのコピーを作成"
      >
        <SubmitButton
          name="コピーを作成"
          disabled={!entries || submitting || submitted}
          isSubmitting={submitting}
          handleSubmit={handleCopy}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <Container>
        {entry.value && (
          <CopyForm
            entries={entries}
            setEntries={setEntries}
            templateEntry={entry.value}
          />
        )}
      </Container>

      <Prompt
        when={edited && !submitted}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
