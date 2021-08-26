import React from "react";
import { useParams, Link } from "react-router-dom";
import Typography from "@material-ui/core/Typography";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import { getEntry } from "../utils/AironeAPIClient";
import { useAsync } from "react-use";
import EntryForm from "../components/entry/EntryForm";

export default function EditEntry({}) {
  const { entityId, entryId } = useParams();

  const entry = useAsync(async () => {
    if (entryId !== undefined) {
      return getEntry(entityId, entryId);
    }
    return Promise.resolve({});
  });

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to="/new-ui/entities">
          エンティティ一覧
        </Typography>
        <Typography
          component={Link}
          to={`/new-ui/entities/${entityId}/entries`}
        >
          {entityId}
        </Typography>
        <Typography color="textPrimary">編集</Typography>
      </AironeBreadcrumbs>

      {!entry.loading && (
        <EntryForm
          entityId={entityId}
          entryId={entityId}
          initName={entry.value.name}
          initAttributes={entry.value.attributes}
        />
      )}
    </div>
  );
}
