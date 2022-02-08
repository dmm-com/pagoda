import { Box, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { groupsPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { GroupForm } from "components/group/GroupForm";
import { getUsers } from "utils/AironeAPIClient";

export const EditGroup: FC = () => {
  const { groupId } = useParams<{ groupId: number }>();

  const users = useAsync(async () => {
    const resp = await getUsers();
    return await resp.json();
  });
  const group = useAsync(async () => {
    return groupId != undefined
      ? await aironeApiClientV2.getGroup(groupId)
      : undefined;
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

      {users.loading || group.loading ? (
        <Loading />
      ) : (
        <GroupForm users={users.value} group={group.value} />
      )}
    </Box>
  );
};
