import { Box } from "@material-ui/core";
import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath } from "../Routes";
import { ACLForm } from "../components/common/ACLForm";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { getACL } from "../utils/AironeAPIClient";

export function ACL({}) {
  const { entityId } = useParams();

  const acl = useAsync(async () => {
    const resp = await getACL(entityId);
    return await resp.json();
  });

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ACL</Typography>
      </AironeBreadcrumbs>

      {!acl.loading && (
        <>
          <Typography>{acl.value.name} の ACL 設定</Typography>
          <ACLForm objectId={entityId} acl={acl.value} />
        </>
      )}
    </Box>
  );
}
