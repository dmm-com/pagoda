import { Box, Tab, Tabs, Typography } from "@mui/material";
import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useAsync } from "react-use";

import { entitiesPath, entityEntriesPath, topPath } from "../Routes";
import { ACLForm } from "../components/common/ACLForm";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import CopyForm from "../components/entry/CopyForm";
import { EntryAttributes } from "../components/entry/EntryAttributes";
import { EntryForm } from "../components/entry/EntryForm";
import EntryHistory from "../components/entry/EntryHistory";
import EntryReferral from "../components/entry/EntryReferral";
import {
  getACL,
  getEntry,
  getEntryHistory,
  getReferredEntries,
} from "../utils/AironeAPIClient";

export function ShowEntry({}) {
  const { entryId } = useParams();

  const [tabValue, setTabValue] = useState(0);

  // TODO get an entry only if show/edit pages
  const entry = useAsync(async () => {
    const resp = await getEntry(entryId);
    if (!resp.ok) {
      throw new Error("entry not found");
    }
    return await resp.json();
  });

  const entryHistory = useAsync(async () => {
    return await getEntryHistory(entryId);
  });

  const referredEntries = useAsync(async () => {
    const resp = await getReferredEntries(entryId);
    const data = await resp.json();
    return data.entries;
  });

  const acl = useAsync(async () => {
    const resp = await getACL(entryId);
    return await resp.json();
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
        <Typography color="textPrimary">{entryId}</Typography>
      </AironeBreadcrumbs>

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
        <Tab label="表示" index={0} />
        <Tab label="編集" index={1} />
        <Tab label="参照エントリ一覧" index={2} />
        <Tab label="変更履歴" index={3} />
        <Tab label="コピー" index={4} />
        <Tab label="ACL設定" index={5} />
      </Tabs>

      <Box hidden={tabValue !== 0}>
        {!entry.loading && <EntryAttributes attributes={entry.value.attrs} />}
      </Box>

      <Box hidden={tabValue !== 1}>
        {!entry.loading && (
          <EntryForm
            entityId={entry.value.schema.id}
            initName={entry.value.name}
            initAttributes={entry.value.attrs}
          />
        )}
      </Box>

      <Box hidden={tabValue !== 2}>
        {!entry.loading && !referredEntries.loading && (
          <EntryReferral
            entityId={entry.value.schema.id}
            referredEntries={referredEntries.value}
          />
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
}
