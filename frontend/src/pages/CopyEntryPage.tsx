import AppsIcon from "@mui/icons-material/Apps";
import { Box, Container, IconButton, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
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
import { CopyForm } from "components/entry/CopyForm";
import { FailedToGetEntry } from "utils/Exceptions";

export const CopyEntryPage: FC = () => {
  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();

  const [entryAnchorEl, setEntryAnchorEl] =
    useState<HTMLButtonElement | null>();

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

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        <Typography
          component={Link}
          to={entityEntriesPath(entry.value.schema.id)}
        >
          {entry.value.schema.name}
        </Typography>
        <Typography
          component={Link}
          to={entryDetailsPath(entry.value.schema.id, entry.value.id)}
        >
          {entry.value.name}
        </Typography>
        <Typography>コピー</Typography>
      </AironeBreadcrumbs>

      <Container maxWidth="lg" sx={{ pt: "112px" }}>
        <Box display="flex">
          <Box width="50px" />
          <Box flexGrow="1">
            <Typography variant="h2" align="center">
              {entry.value.name}
            </Typography>
            <Typography variant="h4" align="center">
              エントリのコピーを作成
            </Typography>
            <Typography align="center" mt="16px" mb="60px">
              入力した各行ごとに{entry.value.name}
              と同じ属性を持つ別のエントリを作成
            </Typography>
          </Box>
          <Box width="50px">
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
        </Box>
      </Container>

      <Box sx={{ borderTop: 1, borderColor: "#0000008A" }}>
        <CopyForm entityId={entry.value.schema.id} entryId={entry.value.id} />
      </Box>
    </Box>
  );
};
