import { Box, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { Loading } from "../components/common/Loading";
import { CopyForm } from "../components/entry/CopyForm";

import {
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
  topPath,
} from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";

export const CopyEntryPage: FC = () => {
  const { entryId } = useParams<{ entryId: number }>();

  const entry = useAsync(async () => {
    return await aironeApiClientV2.getEntry(entryId);
  }, [entryId]);

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

      <CopyForm entityId={entry.value.schema.id} entryId={entry.value.id} />
    </Box>
  );
};
