import { RoleCreateUpdate } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Container, Typography } from "@mui/material";
import { FC, useCallback, useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { RoleForm } from "components/role/RoleForm";
import { Schema, schema } from "components/role/roleForm/RoleFormSchema";
import { useFormNotification } from "hooks/useFormNotification";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { usePrompt } from "hooks/usePrompt";
import { useTranslation } from "hooks/useTranslation";
import { useTypedParams } from "hooks/useTypedParams";
import { translate } from "i18n/config";
import { aironeApiClient } from "repository/AironeApiClient";
import { rolesPath, topPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";
import { ForbiddenError } from "services/Exceptions";

export const RoleEditPage: FC = () => {
  const { roleId } = useTypedParams<{ roleId?: number }>({ allowEmpty: true });
  const willCreate = roleId == null;

  const navigate = useNavigate();
  const { t } = useTranslation();
  const { enqueueSubmitResult } = useFormNotification(
    t("common.target.role"),
    willCreate,
  );

  const { data: role, isLoading: roleLoading } = usePagodaSWR(
    roleId != null ? ["role", roleId] : null,
    () => aironeApiClient.getRole(roleId!),
  );

  // Fill schema-required defaults for optional API fields.
  const initialValues: Schema | undefined = useMemo(
    () =>
      role != null ? { ...role, isActive: role.isActive ?? true } : undefined,
    [role],
  );

  const {
    formState: { isValid, isDirty, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    setError,
    setValue,
    control,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onBlur",
    // Sync form values when the fetched role arrives. Dirty fields are
    // kept so a background revalidation does not clobber user edits.
    values: initialValues,
    resetOptions: { keepDirtyValues: true },
  });

  usePrompt(isDirty && !isSubmitSuccessful, t("role.edit.confirmLeave"));

  useEffect(() => {
    if (!roleLoading && role && !role.isEditable) {
      throw new ForbiddenError("Only admin can edit a role");
    }
  }, [role, roleLoading]);

  useEffect(() => {
    isSubmitSuccessful && navigate(rolesPath());
  }, [isSubmitSuccessful, navigate]);

  usePageTitle(
    roleLoading ? t("role.edit.loading") : TITLE_TEMPLATES.roleEdit,
    {
      prefix:
        role?.name ?? (willCreate ? t("role.edit.newRolePrefix") : undefined),
    },
  );

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
            (message) =>
              enqueueSubmitResult(
                false,
                translate("role.edit.submitFailureDetail", { message }),
              ),
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
    [roleId, enqueueSubmitResult, setError, willCreate],
  );

  const handleCancel = async () => {
    navigate(-1);
  };

  if (roleLoading) {
    return <Loading />;
  }

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={rolesPath()}>
          {t("role.listPage.pageTitle")}
        </Typography>
        <Typography color="textPrimary">{t("role.edit.breadcrumb")}</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={role != null ? role.name : t("role.edit.pageTitleNew")}
        description={role != null ? t("role.edit.description") : undefined}
      >
        <SubmitButton
          name={t("common.save")}
          disabled={
            !isDirty ||
            !isValid ||
            isSubmitting ||
            isSubmitSuccessful ||
            role?.isEditable === false
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
