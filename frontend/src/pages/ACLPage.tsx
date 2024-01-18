import {
  ACLObjtypeEnum,
  EntityDetail,
  EntryRetrieve,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Container } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useCallback, useEffect, useState } from "react";
import { FieldErrors, useForm } from "react-hook-form";
import { Prompt, useHistory } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { editEntityPath, entityEntriesPath, entryDetailsPath } from "Routes";
import { ACLForm } from "components/acl/ACLForm";
import { Schema, schema } from "components/acl/aclForm/ACLFormSchema";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

export const ACLPage: FC = () => {
  const history = useHistory();
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

  const acl = useAsyncWithThrow(async () => {
    return await aironeApiClient.getAcl(objectId);
  });

  const historyReplace = () => {
    switch (acl.value?.objtype) {
      case ACLObjtypeEnum.Entity:
        if (entity?.id) {
          history.replace(entityEntriesPath(entity?.id));
        }
        break;
      case ACLObjtypeEnum.EntityAttr:
        if (entity?.id) {
          history.replace(editEntityPath(entity?.id));
        }
        break;
      case ACLObjtypeEnum.Entry:
        if (entry?.id) {
          history.replace(entryDetailsPath(entry?.schema.id, entry?.id));
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

      <Prompt
        when={isDirty && !isSubmitSuccessful}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
