import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link, useParams } from "react-router-dom";

import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { ImportForm } from "../components/common/ImportForm";
import { importEntries } from "../utils/AironeAPIClient";

export function ImportEntry({}) {
  const { entityId } = useParams();

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
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      <ImportForm
        importFunc={importEntries.bind(null, entityId)}
        redirectPath={`/new-ui/entities/${entityId}/entries`}
      />
    </div>
  );
}
