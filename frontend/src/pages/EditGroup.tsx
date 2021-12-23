import { Box, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { groupsPath, topPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { GroupForm } from "../components/group/GroupForm";
import { getGroup, getUsers } from "../utils/AironeAPIClient";

export const EditGroup: FC = () => {
  const { groupId } = useParams<{ groupId: number }>();

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
    <Box>
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
    </Box>
  );
};
