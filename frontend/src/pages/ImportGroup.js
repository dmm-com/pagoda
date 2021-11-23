import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link } from "react-router-dom";

import { groupsPath, newGroupPath, topPath } from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";
import { ImportForm } from "../components/common/ImportForm.tsx";
import { importGroups } from "../utils/AironeAPIClient.ts";

export function ImportGroup({}) {
  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={newGroupPath()}>
          グループ管理
        </Typography>
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      <ImportForm importFunc={importGroups} redirectPath={groupsPath()} />
    </div>
  );
}
