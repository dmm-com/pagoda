import React from "react";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { Link, useParams } from "react-router-dom";
import { importEntries } from "../utils/AironeAPIClient";
import { ImportForm } from "../components/common/ImportForm";

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
