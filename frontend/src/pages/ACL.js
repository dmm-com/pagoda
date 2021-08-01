import React from "react";
import { getACL } from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";
import ACLForm from "../components/common/ACLForm";

export default function ACL({}) {
  const { entityId } = useParams();

  const acl = useAsync(async () => {
    return getACL(entityId);
  });

  return (
    <div className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography color="textPrimary">ACL</Typography>
      </AironeBreadcrumbs>

      {!acl.loading && (
        <>
          <Typography>{acl.value.object.name} の ACL 設定</Typography>
          <ACLForm acl={acl.value} />
        </>
      )}
    </div>
  );
}
