import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link } from "react-router-dom";

import { topPath, usersPath } from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";
import { ImportForm } from "../components/common/ImportForm.tsx";
import { importGroups } from "../utils/AironeAPIClient.ts";

export function ImportUser({}) {
  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={usersPath()}>
          ユーザ管理
        </Typography>
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      {/* call the 'groups' exporter, not for 'users' */}
      <ImportForm importFunc={importGroups} redirectPath={usersPath()} />
    </div>
  );
}
