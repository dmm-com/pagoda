import React from "react";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import { importEntities } from "../utils/AironeAPIClient";
import ImportForm from "../components/common/ImportForm";

export default function ImportEntity({}) {
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
