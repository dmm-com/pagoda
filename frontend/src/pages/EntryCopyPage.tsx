import { Box, Container } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import {
  CopyForm as DefaultCopyForm,
  CopyFormProps,
} from "components/entry/CopyForm";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { usePrompt } from "hooks/usePrompt";
import { aironeApiClient } from "repository/AironeApiClient";
import { entityEntriesPath, entryDetailsPath } from "routes/Routes";

interface Props {
  CopyForm?: FC<CopyFormProps>;
}

export const EntryCopyPage: FC<Props> = ({ CopyForm = DefaultCopyForm }) => {
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

  usePrompt(
    edited && !submitted,
    "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
  );

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
      enqueueSnackbar("アイテムコピーのジョブ登録が成功しました", {
        variant: "success",
      });
      setTimeout(() => {
        navigate(entityEntriesPath(entityId), { replace: true });
      }, 0.1);
    } catch {
      enqueueSnackbar("アイテムコピーのジョブ登録が失敗しました", {
        variant: "error",
      });
    }
  };

  const handleCancel = () => {
    navigate(
      entryDetailsPath(entry.value?.schema?.id ?? 0, entry.value?.id ?? 0),
      { replace: true }
    );
  };

  return (
    <Box>
      <EntryBreadcrumbs entry={entry.value} title="コピー" />

      <PageHeader
        title={entry.value?.name ?? ""}
        description="アイテムのコピーを作成"
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
    </Box>
  );
};
