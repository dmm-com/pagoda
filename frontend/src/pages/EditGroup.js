import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { groupsPath, topPath } from "../Routes.ts";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs.tsx";
import { GroupForm } from "../components/group/GroupForm.tsx";
import { getGroup, getUsers } from "../utils/AironeAPIClient.ts";

export function EditGroup({}) {
  let { groupId } = useParams();

  const users = useAsync(async () => {
    const resp = await getUsers();
    return await resp.json();
  });
  const group = useAsync(async () => {
    if (groupId !== undefined) {
      const resp = await getGroup(groupId);
      return await resp.json();
    }
  });

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={groupsPath()}>
          グループ管理
        </Typography>
        <Typography color="textPrimary">グループ編集</Typography>
      </AironeBreadcrumbs>

      {!users.loading && !group.loading && (
        <GroupForm users={users.value} group={group.value} />
      )}
    </div>
  );
}
