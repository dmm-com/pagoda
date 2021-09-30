import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link } from "react-router-dom";

import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { ImportForm } from "../components/common/ImportForm";
import { importEntities } from "../utils/AironeAPIClient";

export function ImportEntity({}) {
  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to="/new-ui/entities">
          エンティティ一覧
        </Typography>
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      <ImportForm
        importFunc={importEntities}
        redirectPath={"/new-ui/entities"}
      />
    </div>
  );
}
