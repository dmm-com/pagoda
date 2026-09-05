import { ACLObjtypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Container, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, Suspense, useCallback, useEffect, useMemo } from "react";
import { FieldErrors, useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { usePagodaSWR } from "../hooks/usePagodaSWR";

import { AironeBreadcrumbs, AironeLink } from "components";
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

const ACLEditContent: FC<{ objectId: number }> = ({ objectId }) => {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const { data: acl } = usePagodaSWR(
    ["acl", objectId],
    () => aironeApiClient.getAcl(objectId),
    { suspense: true },
  );

  // Initialize form values from the fetched acl. Dirty fields are kept so a
  // background revalidation does not clobber user edits.
  const initialValues = useMemo(
    () => ({
      isPublic: acl.isPublic ?? false,
      defaultPermission: acl.defaultPermission,
      objtype: acl.objtype,
      roles: acl.roles,
    }),
    [acl],
  );

  const {
    formState: { isDirty, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    control,
    watch,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onSubmit",
    // Sync form values when the fetched acl arrives.
    values: initialValues,
    resetOptions: { keepDirtyValues: true },
  });

  usePrompt(
    isDirty && !isSubmitSuccessful,
    "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
  );

  // Fetch the parent/self entity or entry that the breadcrumbs and
  // cancel-navigation need, depending on the ACL object type.
  const entityId = (() => {
    switch (acl.objtype) {
      case ACLObjtypeEnum.Entity:
        return objectId;
      case ACLObjtypeEnum.EntityAttr:
        return acl.parent?.id;
      default:
        return undefined;
    }
  })();

  // One-shot page context (breadcrumbs / navigation target); no need to
  // track server freshness on window focus.
  const { data: entity } = usePagodaSWR(
    entityId != null ? ["entity", entityId] : null,
    () => aironeApiClient.getEntity(entityId ?? 0),
    { revalidateOnFocus: false },
  );

  const { data: entry } = usePagodaSWR(
    acl.objtype === ACLObjtypeEnum.Entry ? ["entry", objectId] : null,
    () => aironeApiClient.getEntry(objectId),
    { revalidateOnFocus: false },
  );

  // Derived from fetched data; no state needed.
  const breadcrumbs = (() => {
    switch (acl.objtype) {
      case ACLObjtypeEnum.Category:
        return (
          <AironeBreadcrumbs>
            <Typography component={AironeLink} to={topPath()}>
              Top
            </Typography>
            <Typography component={AironeLink} to={listCategoryPath()}>
              カテゴリ一覧
            </Typography>
            <Typography color="textPrimary">{acl.name}</Typography>
            <Typography color="textPrimary">ACL設定</Typography>
          </AironeBreadcrumbs>
        );
      case ACLObjtypeEnum.Entity:
        return entity != null ? (
          <EntityBreadcrumbs entity={entity} title="ACL設定" />
        ) : (
          <Box />
        );
      case ACLObjtypeEnum.EntityAttr:
        return entity != null ? (
          <EntityBreadcrumbs entity={entity} attr={acl.name} title="ACL設定" />
        ) : (
          <Box />
        );
      case ACLObjtypeEnum.Entry:
        return entry != null ? (
          <EntryBreadcrumbs entry={entry} title="ACL設定" />
        ) : (
          <Box />
        );
      default:
        return <Box />;
    }
  })();

  const historyReplace = useCallback(() => {
    switch (acl.objtype) {
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
          navigate(entryDetailsPath(entry.schema.id, entry.id), {
            replace: true,
          });
        }
        break;
    }
  }, [acl.objtype, entity, entry, navigate]);

  const handleSubmitOnInvalid = useCallback(
    async (err: FieldErrors<Schema & { generalError: string }>) => {
      err.generalError &&
        enqueueSnackbar(err.generalError.message, { variant: "error" });
    },
    [enqueueSnackbar],
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
        aclForm.defaultPermission,
      );

      enqueueSnackbar("ACL設定の更新が成功しました", { variant: "success" });
    },
    [objectId, enqueueSnackbar],
  );

  const handleCancel = async () => {
    historyReplace();
  };

  // Navigate after the submit succeeded. This must stay in an effect so that
  // the usePrompt blocker is disabled (isSubmitSuccessful=true) before leaving.
  useEffect(() => {
    if (isSubmitSuccessful) {
      historyReplace();
    }
  }, [isSubmitSuccessful, historyReplace]);

  return (
    <>
      {breadcrumbs}

      <PageHeader title={acl.name} description="ACL設定">
        <SubmitButton
          name="保存"
          disabled={isSubmitting || isSubmitSuccessful}
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(
            handleSubmitOnValid,
            handleSubmitOnInvalid,
          )}
          handleCancel={handleCancel}
        />
      </PageHeader>

      {isSubmitting ? (
        <Loading />
      ) : (
        <Container>
          <ACLForm control={control} watch={watch} />
        </Container>
      )}
    </>
  );
};

export const ACLEditPage: FC = () => {
  const { objectId } = useTypedParams<{ objectId: number }>();

  return (
    <Box className="container-fluid">
      <Suspense fallback={<Loading />}>
        <ACLEditContent objectId={objectId} />
      </Suspense>
    </Box>
  );
};
