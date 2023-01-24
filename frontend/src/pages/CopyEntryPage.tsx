import LockIcon from "@mui/icons-material/Lock";
import { Box, Container, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { Link, Prompt, useHistory } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import {
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
  topPath,
} from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { CopyForm } from "components/entry/CopyForm";

export const CopyEntryPage: FC = () => {
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();

  // newline delimited string value, not string[]
  const [entries, _setEntries] = useState<string>("");
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [edited, setEdited] = useState<boolean>(false);

  const entry = useAsyncWithThrow(async () => {
    return await aironeApiClientV2.getEntry(entryId);
  }, [entryId]);

  if (entry.loading) {
    return <Loading />;
  }

  const setEntries = (entries: string) => {
    setEdited(true);
    _setEntries(entries);
  };

  const handleCopy = async () => {
    await aironeApiClientV2
      .copyEntry(entryId, entries.split("\n"))
      .then(() => {
        setSubmitted(true);
        enqueueSnackbar("エントリコピーのジョブ登録が成功しました", {
          variant: "success",
        });
        history.replace(entityEntriesPath(entityId));
      })
      .catch(() => {
        enqueueSnackbar("エントリコピーのジョブ登録が失敗しました", {
          variant: "error",
        });
      });
  };

  const handleCancel = () => {
    history.replace(entryDetailsPath(entry.value.schema.id, entry.value.id));
  };

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        <Box sx={{ display: "flex" }}>
          <Typography
            component={Link}
            to={entityEntriesPath(entry.value.schema.id)}
          >
            {entry.value?.schema?.name}
          </Typography>
          {entry.value?.schema?.isPublic === false && <LockIcon />}
        </Box>
        <Box sx={{ display: "flex" }}>
          <Typography
            component={Link}
            to={entryDetailsPath(entry.value.schema.id, entry.value.id)}
          >
            {entry.value?.name}
          </Typography>
          {entry.value?.isPublic === false && <LockIcon />}
        </Box>
        <Typography>コピー</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={entry.value?.name ?? ""}
        description="エントリのコピーを作成"
      >
        <SubmitButton
          name="コピーを作成"
          disabled={!entries}
          handleSubmit={handleCopy}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <Container>
        <Typography>
          {"入力した各行ごとに " +
            entry.value?.name.substring(0, 50) +
            " と同じ属性を持つ別のエントリを作成"}
        </Typography>
        <CopyForm entries={entries} setEntries={setEntries} />
      </Container>

      <Prompt
        when={edited && !submitted}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
