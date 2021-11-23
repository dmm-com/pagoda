import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link } from "react-router-dom";

import { entitiesPath, topPath } from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";
import { ImportForm } from "../components/common/ImportForm.tsx";
import { importEntities } from "../utils/AironeAPIClient.ts";

export function ImportEntity({}) {
  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      <ImportForm importFunc={importEntities} redirectPath={entitiesPath()} />
    </div>
  );
}
