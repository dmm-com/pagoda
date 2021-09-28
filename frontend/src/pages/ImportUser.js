import React from "react";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import { importGroups } from "../utils/AironeAPIClient";
import { ImportForm } from "../components/common/ImportForm";

export function ImportUser({}) {
  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to="/new-ui/users">
          ユーザ管理
        </Typography>
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      {/* call the 'groups' exporter, not for 'users' */}
      <ImportForm importFunc={importGroups} redirectPath={"/new-ui/users"} />
    </div>
  );
}
