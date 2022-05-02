import { Box, Tab, Tabs, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { useTypedParams } from "../hooks/useTypedParams";

import { entitiesPath, entityEntriesPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { ACLForm } from "components/common/ACLForm";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { CopyForm } from "components/entry/CopyForm";
import { EntryAttributes } from "components/entry/EntryAttributes";
import { EntryForm } from "components/entry/EntryForm";
import { EntryHistory } from "components/entry/EntryHistory";
import { EntryReferral } from "components/entry/EntryReferral";
import { getEntryHistory } from "utils/AironeAPIClient";

export const ShowEntryPage: FC = () => {
  const { entryId } = useTypedParams<{ entryId: number }>();

  const [tabValue, setTabValue] = useState(0);

  // TODO get an entry only if show/edit pages
  const entry = useAsync(async () => {
    return await aironeApiClientV2.getEntry(entryId);
  });

  const entryHistory: any = useAsync(async () => {
    return await getEntryHistory(entryId);
  });

  const acl = useAsync(async () => {
    return await aironeApiClientV2.getAcl(entryId);
  });

  if (entry.error !== undefined) {
    return <p>FIX TO SHOW: {entry.error.toString()}</p>;
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
        {!entry.loading && (
          <Typography
            component={Link}
            to={entityEntriesPath(entry.value.schema.id)}
          >
            {entry.value.schema.name}
          </Typography>
        )}
        {!entry.loading && (
          <Typography color="textPrimary">{entry.value.name}</Typography>
        )}
      </AironeBreadcrumbs>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
        <Tab label="表示" />
        <Tab label="編集" />
        <Tab label="参照エントリ一覧" />
        <Tab label="変更履歴" />
        <Tab label="コピー" />
        <Tab label="ACL設定" />
      </Tabs>

      <Box hidden={tabValue !== 0}>
        {!entry.loading && <EntryAttributes attributes={entry.value.attrs} />}
      </Box>

      <Box hidden={tabValue !== 1}>
        {!entry.loading && (
          <EntryForm
            entityId={entry.value.schema.id}
            entryId={entry.value.id}
            initName={entry.value.name}
            initAttributes={entry.value.attrs}
          />
        )}
      </Box>

      <Box hidden={tabValue !== 2}>
        {!entry.loading && (
          <EntryReferral entityId={entry.value.schema.id} entryId={entryId} />
        )}
      </Box>

      <Box hidden={tabValue !== 3}>
        {!entryHistory.loading && (
          <EntryHistory histories={entryHistory.value} />
        )}
      </Box>

      <Box hidden={tabValue !== 4}>
        {!entry.loading && (
          <CopyForm entityId={entry.value.schema.id} entryId={entryId} />
        )}
      </Box>

      <Box hidden={tabValue !== 5}>
        {!acl.loading && <ACLForm objectId={entryId} acl={acl.value} />}
      </Box>
    </Box>
  );
};
