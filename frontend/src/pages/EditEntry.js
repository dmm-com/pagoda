import Typography from "@material-ui/core/Typography";
import React from "react";
import { useParams, Link } from "react-router-dom";
import { useAsync } from "react-use";

import { entitiesPath, entityEntriesPath, topPath } from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";
import { EntryForm } from "../components/entry/EntryForm.tsx";
import { getEntry } from "../utils/AironeAPIClient.ts";

export function EditEntry({}) {
  const { entityId, entryId } = useParams();

  const entry = useAsync(async () => {
    if (entryId !== undefined) {
      return await getEntry(entryId);
    }
    return {};
  });

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        <Typography component={Link} to={entityEntriesPath(entityId)}>
          {entityId}
        </Typography>
        <Typography color="textPrimary">編集</Typography>
      </AironeBreadcrumbs>

      {!entry.loading && (
        <EntryForm
          entityId={Number(entityId)}
          initName={entry.value.name}
          initAttributes={entry.value.attributes}
        />
      )}
    </div>
  );
}
