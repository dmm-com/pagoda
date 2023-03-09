import { zodResolver } from "@hookform/resolvers/zod";
import LockIcon from "@mui/icons-material/Lock";
import { Box, Container, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, Prompt, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { schema, Schema } from "../components/acl/ACLFormSchema";
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
import { DjangoContext } from "services/DjangoContext";

export const ACLPage: FC = () => {
  const djangoContext = DjangoContext.getInstance();
  const history = useHistory();
  const { enqueueSnackbar } = useSnackbar();
  const { objectId } = useTypedParams<{ objectId: number }>();

  const {
    formState: { isDirty, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    reset,
    control,
    watch,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onSubmit",
  });

  const acl = useAsync(async () => {
    return await aironeApiClientV2.getAcl(objectId);
  });

  const handleSubmitOnInvalid = useCallback(
    async (err) => {
      enqueueSnackbar(err.generalError.message, { variant: "error" });
    },
    [objectId]
  );

  const handleSubmitOnValid = useCallback(
    async (aclForm: Schema) => {
      const aclSettings =
        aclForm.roles.map((role) => ({
          member_id: role.id,
          value: role.currentPermission,
        })) ?? [];

      await aironeApiClientV2.updateAcl(
        objectId,
        aclForm.isPublic,
        aclSettings,
        aclForm.objtype,
        aclForm.defaultPermission
      );

      enqueueSnackbar("ACL 設定の更新が成功しました", { variant: "success" });
      history.goBack();
    },
    [objectId]
  );

  const handleCancel = async () => {
    history.goBack();
  };

  /* initialize permissions and isPublic variables from acl parameter */
  useEffect(() => {
    reset({
      isPublic: acl.value?.isPublic,
      defaultPermission: acl.value?.defaultPermission,
      objtype: acl.value?.objtype,
      roles: acl.value?.roles,
    });
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
            {((acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entity ?? 0)) >
              0 && (
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
            {((acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entry ?? 0)) >
              0 && (
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
            {((acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entry ?? 0)) >
              0 && (
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
            {((acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entityAttr ?? 0)) >
              0 && (
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
            {((acl.value.objtype ?? 0) &
              (djangoContext?.aclObjectType.entityAttr ?? 0)) >
              0 && (
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
          disabled={isSubmitting || isSubmitSuccessful}
          handleSubmit={handleSubmit(
            handleSubmitOnValid,
            handleSubmitOnInvalid
          )}
          handleCancel={handleCancel}
        />
      </PageHeader>

      {acl.loading ? (
        <Loading />
      ) : (
        <Container>
          <ACLForm control={control} watch={watch} />
        </Container>
      )}

      <Prompt
        when={isDirty && !isSubmitSuccessful}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
