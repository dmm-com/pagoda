import { RoleCreateUpdate } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Container, Typography } from "@mui/material";
import React, { FC, useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { RoleForm } from "components/role/RoleForm";
import { Schema, schema } from "components/role/roleForm/RoleFormSchema";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { useFormNotification } from "hooks/useFormNotification";
import { usePageTitle } from "hooks/usePageTitle";
import { usePrompt } from "hooks/usePrompt";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { rolesPath, topPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";
import { ForbiddenError } from "services/Exceptions";

export const RoleEditPage: FC = () => {
  const { roleId } = useTypedParams<{ roleId?: number }>();
  const willCreate = roleId == null;

  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification("ロール", willCreate);

  const {
    formState: { isValid, isDirty, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    reset,
    setError,
    setValue,
    control,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onBlur",
  });

  usePrompt(
    isDirty && !isSubmitSuccessful,
    "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
  );

  const role = useAsyncWithThrow(async () => {
    return roleId != null ? await aironeApiClient.getRole(roleId) : undefined;
  }, [roleId]);

  useEffect(() => {
    if (!role.loading && role.value && !role.value.isEditable) {
      throw new ForbiddenError("Only admin can edit a role");
    }
  }, [role]);

  useEffect(() => {
    !role.loading && role.value != null && reset(role.value);
  }, [role.loading]);

  useEffect(() => {
    isSubmitSuccessful && navigate(rolesPath());
  }, [isSubmitSuccessful]);

  usePageTitle(role.loading ? "読み込み中..." : TITLE_TEMPLATES.roleEdit, {
    prefix: role.value?.name ?? (willCreate ? "新規作成" : undefined),
  });

  const handleSubmitOnValid = useCallback(
    async (role: Schema) => {
      const roleCreateUpdate: RoleCreateUpdate = {
        ...role,
        users: role.users.map((user) => user.id),
        groups: role.groups.map((group) => group.id),
        adminUsers: role.adminUsers.map((user) => user.id),
        adminGroups: role.adminGroups.map((group) => group.id),
      };

      try {
        if (willCreate) {
          await aironeApiClient.createRole(roleCreateUpdate);
        } else {
          await aironeApiClient.updateRole(roleId, roleCreateUpdate);
        }
        enqueueSubmitResult(true);
      } catch (e) {
        if (e instanceof Error && isResponseError(e)) {
          await extractAPIException<Schema>(
            e,
            (message) => enqueueSubmitResult(false, `詳細: "${message}"`),
            (name, message) => {
              setError(name, { type: "custom", message: message });
              enqueueSubmitResult(false);
            },
          );
        } else {
          enqueueSubmitResult(false);
        }
      }
    },
    [roleId],
  );

  const handleCancel = async () => {
    navigate(-1);
  };

  if (role.loading) {
    return <Loading />;
  }

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={rolesPath()}>
          ロール管理
        </Typography>
        <Typography color="textPrimary">ロール編集</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={role.value != null ? role.value.name : "新規ロールの作成"}
        description={role.value != null ? "ロール編集" : undefined}
      >
        <SubmitButton
          name="保存"
          disabled={
            !isDirty ||
            !isValid ||
            isSubmitting ||
            isSubmitSuccessful ||
            role.value?.isEditable === false
          }
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(handleSubmitOnValid)}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <Container>
        <RoleForm control={control} setValue={setValue} />
      </Container>
    </Box>
  );
};
