import LockIcon from "@mui/icons-material/Lock";
import { Box, Container, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useEffect, useState } from "react";
import { Link, Prompt, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { PageHeader } from "../components/common/PageHeader";
import { useTypedParams } from "../hooks/useTypedParams";

import {
  topPath,
  entityEntriesPath,
  entryDetailsPath,
  entitiesPath,
} from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { ACLForm } from "components/common/ACLForm";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { SubmitButton } from "components/common/SubmitButton";
import { DjangoContext } from "utils/DjangoContext";

export const ACLPage: FC = () => {
  const djangoContext = DjangoContext.getInstance();
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
  const { objectId } = useTypedParams<{ objectId: number }>();

  const [submittable, setSubmittable] = useState<boolean>(false);
  const [aclInfo, _setACLInfo] = useState({
    isPublic: false,
    defaultPermission: 1,
    permissions: {},
  });
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [edited, setEdited] = useState<boolean>(false);

  const acl = useAsync(async () => {
    return await aironeApiClientV2.getAcl(objectId);
  });

  const setACLInfo = (aclInfo: {
    isPublic: boolean;
    defaultPermission: number;
    permissions: object;
  }) => {
    setEdited(true);
    _setACLInfo(aclInfo);
  };

  const handleSubmit = async () => {
    // TODO better name?
    if (!acl.loading) {
      const aclSettings =
        acl.value?.roles.map((role) => {
          return {
            member_id: role.id,
            value: aclInfo.permissions[role.id]?.current_permission,
          };
        }) ?? [];

      await aironeApiClientV2.updateAcl(
        objectId,
        acl.value.name,
        acl.value.objtype,
        aclInfo.isPublic,
        aclInfo.defaultPermission,
        aclSettings
      );
      setSubmitted(true);

      enqueueSnackbar("ACL 設定の更新が成功しました", { variant: "success" });
      history.goBack();
    }
  };

  const handleCancel = async () => {
    history.goBack();
  };

  /* initialize permissions and isPublic variables from acl parameter */
  useEffect(() => {
    if (!acl.loading && acl.value != null) {
      _setACLInfo({
        isPublic: acl.value.isPublic ?? false,
        defaultPermission: acl.value.defaultPermission,
        permissions: acl.value.roles.reduce((obj, role) => {
          return {
            ...obj,
            [role.id]: role,
          };
        }, {}),
      });
    }
  }, [acl]);

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>

        {!acl.loading && acl.value != null && (
          <>
            {/* This is a statement for Entity */}
            {(acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entity ?? 0) && (
              <Box sx={{ display: "flex" }}>
                <Typography
                  component={Link}
                  to={entityEntriesPath(acl.value.id)}
                >
                  {acl.value?.name}
                </Typography>
                {acl.value?.isPublic === false && <LockIcon />}
              </Box>
            )}

            {/* This is a statement for Entry */}
            {(acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entry ?? 0) && (
              <Box sx={{ display: "flex" }}>
                <Typography
                  component={Link}
                  to={entityEntriesPath(acl.value.parent?.id ?? 0)}
                >
                  {acl.value?.parent?.name}
                </Typography>
                {acl.value?.parent?.isPublic === false && <LockIcon />}
              </Box>
            )}
            {(acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entry ?? 0) && (
              <Box sx={{ display: "flex" }}>
                <Typography
                  component={Link}
                  to={entryDetailsPath(acl.value.parent?.id ?? 0, acl.value.id)}
                >
                  {acl.value?.name}
                </Typography>
                {acl.value?.isPublic === false && <LockIcon />}
              </Box>
            )}

            {/* This is a statement for EntityAttr */}
            {(acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entityAttr ?? 0) && (
              <Box sx={{ display: "flex" }}>
                <Typography
                  component={Link}
                  to={entityEntriesPath(acl.value.parent?.id ?? 0)}
                >
                  {acl.value?.parent?.name}
                </Typography>
                {acl.value?.parent?.isPublic === false && <LockIcon />}
              </Box>
            )}
            {(acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entityAttr ?? 0) && (
              <Box sx={{ display: "flex" }}>
                <Typography color="textPrimary">{acl.value?.name}</Typography>
                {acl.value?.isPublic === false && <LockIcon />}
              </Box>
            )}

            {/* This is a statement for EntryAttr */}
          </>
        )}
        <Typography color="textPrimary">ACL</Typography>
      </AironeBreadcrumbs>

      <PageHeader title={acl.value?.name ?? ""} description="ACL設定">
        <SubmitButton
          name="保存"
          disabled={!submittable}
          handleSubmit={handleSubmit}
          handleCancel={handleCancel}
        />
      </PageHeader>

      {acl.loading ? (
        <Loading />
      ) : (
        <Container>
          <ACLForm
            aclInfo={aclInfo}
            setACLInfo={setACLInfo}
            setSubmittable={setSubmittable}
          />
        </Container>
      )}

      <Prompt
        when={edited && !submitted}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
