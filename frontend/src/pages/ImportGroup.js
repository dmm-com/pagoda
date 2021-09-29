import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link } from "react-router-dom";

import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { ImportForm } from "../components/common/ImportForm";
import { importGroups } from "../utils/AironeAPIClient";

export function ImportGroup({}) {
  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to="/new-ui/groups">
          グループ管理
        </Typography>
        <Typography>インポート</Typography>
      </AironeBreadcrumbs>

      <ImportForm importFunc={importGroups} redirectPath={"/new-ui/groups"} />
    </div>
  );
}
