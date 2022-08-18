import { Box, Button, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { PageHeader } from "../components/common/PageHeader";
import { useTypedParams } from "../hooks/useTypedParams";

import { topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { ACLForm } from "components/common/ACLForm";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";

export const ACLPage: FC = () => {
  const { objectId } = useTypedParams<{ objectId: number }>();
  const [submittable, setSubmittable] = useState<boolean>(false);

  const acl = useAsync(async () => {
    return await aironeApiClientV2.getAcl(objectId);
  });

  const handleSubmit = async () => {
    return undefined;
  };
  const handleCancel = async () => {
    return undefined;
  };

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">ACL</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={acl.value?.name}
        subTitle="ACL設定"
        componentSubmits={
          <Box display="flex" justifyContent="center">
            <Box mx="4px">
              <Button
                variant="contained"
                color="secondary"
                disabled={!submittable}
                onClick={handleSubmit}
              >
                保存
              </Button>
            </Box>
            <Box mx="4px">
              <Button variant="outlined" color="primary" onClick={handleCancel}>
                キャンセル
              </Button>
            </Box>
          </Box>
        }
      />

      {acl.loading ? (
        <Loading />
      ) : (
        <Box
          sx={{ marginTop: "111px", paddingLeft: "10%", paddingRight: "10%" }}
        >
          <ACLForm
            objectId={objectId}
            acl={acl.value}
            setSubmittable={setSubmittable}
          />
        </Box>
      )}
    </Box>
  );
};
