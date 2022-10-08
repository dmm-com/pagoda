import AppsIcon from "@mui/icons-material/Apps";
import LockIcon from "@mui/icons-material/Lock";
import { Box, IconButton, Typography, Button } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { Link, Prompt, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { EntryControlMenu } from "../components/entry/EntryControlMenu";
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
import { CopyForm } from "components/entry/CopyForm";
import { FailedToGetEntry } from "utils/Exceptions";

export const CopyEntryPage: FC = () => {
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();
  const [entryAnchorEl, setEntryAnchorEl] =
    useState<HTMLButtonElement | null>();
  // newline delimited string value, not string[]
  const [entries, _setEntries] = useState<string>("");
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [edited, setEdited] = useState<boolean>(false);

  const entry = useAsync(async () => {
    return await aironeApiClientV2.getEntry(entryId);
  }, [entryId]);

  if (!entry.loading && entry.error) {
    throw new FailedToGetEntry(
      "Failed to get Entry from AirOne APIv2 endpoint"
    );
  }

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
      .then((resp) => {
        setSubmitted(true);
        enqueueSnackbar("エントリコピーのジョブ登録が成功しました", {
          variant: "success",
        });
        history.replace(entityEntriesPath(entityId));
      })
      .catch((error) => {
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
            {entry.value.schema.name}
          </Typography>
          {!entry.value.schema.isPublic && <LockIcon />}
        </Box>
        <Box sx={{ display: "flex" }}>
          <Typography
            component={Link}
            to={entryDetailsPath(entry.value.schema.id, entry.value.id)}
          >
            {entry.value.name}
          </Typography>
          {!entry.value.isPublic && <LockIcon />}
        </Box>
        <Typography>コピー</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={entry.value.name}
        subTitle="エントリのコピーを作成"
        description={
          "入力した各行ごとに " +
          entry.value.name.substring(0, 50) +
          " と同じ属性を持つ別のエントリを作成"
        }
        componentSubmits={
          <Box display="flex" justifyContent="center">
            <Box mx="4px">
              <Button
                variant="contained"
                color="secondary"
                disabled={!entries}
                onClick={handleCopy}
              >
                コピーを作成
              </Button>
            </Box>
            <Box mx="4px">
              <Button variant="outlined" color="primary" onClick={handleCancel}>
                キャンセル
              </Button>
            </Box>
          </Box>
        }
        componentControl={
          <Box>
            <IconButton
              onClick={(e) => {
                setEntryAnchorEl(e.currentTarget);
              }}
            >
              <AppsIcon />
            </IconButton>
            <EntryControlMenu
              entityId={entityId}
              entryId={entryId}
              anchorElem={entryAnchorEl}
              handleClose={() => setEntryAnchorEl(null)}
            />
          </Box>
        }
      />

      <Box>
        <CopyForm entries={entries} setEntries={setEntries} />
      </Box>

      <Prompt
        when={edited && !submitted}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
