import React from "react";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { Link } from "react-router-dom";
import { importGroups } from "../utils/AironeAPIClient";
import { ImportForm } from "../components/common/ImportForm";

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
