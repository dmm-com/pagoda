import React from "react";
import { Link, useParams } from "react-router-dom";
import Typography from "@material-ui/core/Typography";
import { getGroup, getUsers } from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import { useAsync } from "react-use";
import GroupForm from "../components/group/GroupForm";

export default function EditGroup({}) {
  let { groupId } = useParams();

  const users = useAsync(async () => {
    return getUsers().then((resp) => resp.json());
  });
  const group = useAsync(async () => {
    if (groupId !== undefined) {
      return getGroup(groupId).then((resp) => resp.json());
    }
    return Promise.resolve({});
  });

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to="/new-ui/groups">
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
