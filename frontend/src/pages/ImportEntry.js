import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link, useParams } from "react-router-dom";

import { entitiesPath, entityEntriesPath, topPath } from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";
import { ImportForm } from "../components/common/ImportForm.tsx";
import { importEntries } from "../utils/AironeAPIClient.ts";

export function ImportEntry({}) {
  const { entityId } = useParams();

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
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      <ImportForm
        importFunc={importEntries.bind(null, entityId)}
        redirectPath={entityEntriesPath(entityId)}
      />
    </div>
  );
}
