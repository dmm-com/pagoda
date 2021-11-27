import Typography from "@material-ui/core/Typography";
import React, { FC } from "react";
import { useParams, Link } from "react-router-dom";
import { useAsync } from "react-use";

import { entitiesPath, entityEntriesPath, topPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { EntryForm } from "../components/entry/EntryForm";
import { getEntry } from "../utils/AironeAPIClient";

export const EditEntry: FC = () => {
  const { entityId, entryId } =
    useParams<{ entityId: number; entryId: number }>();

  const entry: any = useAsync(async () => {
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
};
