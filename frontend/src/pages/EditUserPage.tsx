import { Box, Typography, Button } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { useTypedParams } from "../hooks/useTypedParams";

import { topPath, usersPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { UserForm } from "components/user/UserForm";
import { PageHeader } from "components/common/PageHeader";

export const EditUserPage: FC = () => {
  const { userId } = useTypedParams<{ userId: number }>();

  const user = useAsync(async () => {
    if (userId) {
      return await aironeApiClientV2.getUser(userId);
    }
  });

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={usersPath()}>
          ユーザ管理
        </Typography>
        <Typography color="textPrimary">ユーザ情報の設定</Typography>
      </AironeBreadcrumbs>
      <PageHeader
        title={"ユーザ情報の設定"}
        subTitle={""}
        componentSubmits={
          <Box display="flex" justifyContent="center">
            <Box mx="4px">
              <Button
                variant="contained"
                color="secondary"
                onClick={() => {}}
              >
                保存
              </Button>
            </Box>
            <Box mx="4px">
              <Button variant="outlined" color="primary" onClick={() => {}}>
                キャンセル
              </Button>
            </Box>
          </Box>
        }
      />

      {user.loading ? <Loading /> : <UserForm user={user.value} />}
    </Box>
  );
};
