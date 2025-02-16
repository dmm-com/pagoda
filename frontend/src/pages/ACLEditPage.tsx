import {
  ACLObjtypeEnum,
  EntityDetail,
  EntryRetrieve,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Container, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useCallback, useEffect, useState } from "react";
import { FieldErrors, useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { AironeBreadcrumbs } from "components";
import { ACLForm } from "components/acl/ACLForm";
import { Schema, schema } from "components/acl/aclForm/ACLFormSchema";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { usePrompt } from "hooks/usePrompt";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  editEntityPath,
  entityEntriesPath,
  entryDetailsPath,
  listCategoryPath,
  topPath,
} from "routes/Routes";

export const ACLEditPage: FC = () => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { objectId } = useTypedParams<{ objectId: number }>();
  const [entity, setEntity] = useState<EntityDetail>();
  const [entry, setEntry] = useState<EntryRetrieve>();
  const [breadcrumbs, setBreadcrumbs] = useState<JSX.Element>(<Box />);

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

  usePrompt(
    isDirty && !isSubmitSuccessful,
    "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
  );

  const acl = useAsyncWithThrow(async () => {
    return await aironeApiClient.getAcl(objectId);
  });

  const historyReplace = () => {
    switch (acl.value?.objtype) {
      case ACLObjtypeEnum.Category:
        navigate(listCategoryPath(), { replace: true });
        break;
      case ACLObjtypeEnum.Entity:
        if (entity?.id) {
          navigate(entityEntriesPath(entity?.id), { replace: true });
        }
        break;
      case ACLObjtypeEnum.EntityAttr:
        if (entity?.id) {
          navigate(editEntityPath(entity?.id), { replace: true });
        }
        break;
      case ACLObjtypeEnum.Entry:
        if (entry?.id) {
          navigate(entryDetailsPath(entry?.schema.id, entry?.id), {
            replace: true,
          });
        }
        break;
    }
  };

  const handleSubmitOnInvalid = useCallback(
    async (err: FieldErrors<Schema & { generalError: string }>) => {
      err.generalError &&
        enqueueSnackbar(err.generalError.message, { variant: "error" });
    },
    [objectId]
  );

  const handleSubmitOnValid = useCallback(
    async (aclForm: Schema) => {
      const aclSettings =
        aclForm.roles.map((role) => ({
          memberId: role.id,
          value: role.currentPermission,
        })) ?? [];

      await aironeApiClient.updateAcl(
        objectId,
        aclForm.isPublic,
        aclSettings,
        aclForm.objtype,
        aclForm.defaultPermission
      );

      enqueueSnackbar("ACL設定の更新が成功しました", { variant: "success" });
    },
    [objectId]
  );

  const handleCancel = async () => {
    historyReplace();
  };

  /* initialize permissions and isPublic variables from acl parameter */
  useEffect(() => {
    if (acl.value == null) return;
    reset({
      isPublic: acl.value.isPublic,
      defaultPermission: acl.value.defaultPermission,
      objtype: acl.value.objtype,
      roles: acl.value.roles,
    });
    switch (acl.value.objtype) {
      case ACLObjtypeEnum.Category:
        setBreadcrumbs(
          <AironeBreadcrumbs>
            <Typography component={Link} to={topPath()}>
              Top
            </Typography>
            <Typography component={Link} to={listCategoryPath()}>
              カテゴリ一覧
            </Typography>
            <Typography color="textPrimary">{acl.value.name}</Typography>
            <Typography color="textPrimary">ACL設定</Typography>
          </AironeBreadcrumbs>
        );
        break;
      case ACLObjtypeEnum.Entity:
        aironeApiClient.getEntity(objectId).then((resp) => {
          setEntity(resp);
          setBreadcrumbs(<EntityBreadcrumbs entity={resp} title="ACL設定" />);
        });
        break;
      case ACLObjtypeEnum.EntityAttr:
        if (acl.value.parent?.id) {
          aironeApiClient.getEntity(acl.value.parent?.id).then((resp) => {
            setEntity(resp);
            setBreadcrumbs(
              <EntityBreadcrumbs
                entity={resp}
                attr={acl.value?.name}
                title="ACL設定"
              />
            );
          });
        }

        break;
      case ACLObjtypeEnum.Entry:
        aironeApiClient.getEntry(objectId).then((resp) => {
          setEntry(resp);
          setBreadcrumbs(<EntryBreadcrumbs entry={resp} title="ACL設定" />);
        });
        break;
    }
  }, [acl.value]);

  useEffect(() => {
    if (isSubmitSuccessful) {
      historyReplace();
    }
  }, [isSubmitSuccessful]);

  return (
    <Box className="container-fluid">
      {breadcrumbs}

      <PageHeader title={acl.value?.name ?? ""} description="ACL設定">
        <SubmitButton
          name="保存"
          disabled={isSubmitting || isSubmitSuccessful}
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(
            handleSubmitOnValid,
            handleSubmitOnInvalid
          )}
          handleCancel={handleCancel}
        />
      </PageHeader>

      {acl.loading || isSubmitting ? (
        <Loading />
      ) : (
        <Container>
          <ACLForm control={control} watch={watch} />
        </Container>
      )}
    </Box>
  );
};
