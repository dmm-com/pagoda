import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Container, Typography } from "@mui/material";
import { FC, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { GroupForm } from "components/group/GroupForm";
import { schema, Schema } from "components/group/groupForm/GroupFormSchema";
import { useFormNotification } from "hooks/useFormNotification";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { usePrompt } from "hooks/usePrompt";
import { useTranslation } from "hooks/useTranslation";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { groupsPath, topPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";
import { ForbiddenError } from "services/Exceptions";
import { ServerContext } from "services/ServerContext";

export const GroupEditPage: FC = () => {
  const { groupId } = useTypedParams<{ groupId?: number }>({
    allowEmpty: true,
  });
  const willCreate = groupId == null;

  const navigate = useNavigate();
  const { t } = useTranslation();
  const { enqueueSubmitResult } = useFormNotification(
    t("common.target.group"),
    willCreate,
  );

  const { data: group, isLoading: groupLoading } = usePagodaSWR(
    groupId != null ? ["group", groupId] : null,
    () => aironeApiClient.getGroup(groupId!),
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
    // Sync form values when the fetched group arrives. Dirty fields are
    // kept so a background revalidation does not clobber user edits.
    values: group,
    resetOptions: { keepDirtyValues: true },
  });

  usePrompt(isDirty && !isSubmitSuccessful, t("group.edit.confirmLeave"));

  const handleSubmitOnValid = async (group: Schema) => {
    try {
      if (willCreate) {
        await aironeApiClient.createGroup({
          ...group,
          members: group.members.map((member) => member.id),
        });
      } else {
        await aironeApiClient.updateGroup(groupId, {
          ...group,
          members: group.members.map((member) => member.id),
        });
      }
      enqueueSubmitResult(true);
    } catch (e) {
      if (e instanceof Error && isResponseError(e)) {
        await extractAPIException<Schema>(
          e,
          (message) =>
            enqueueSubmitResult(
              false,
              t("group.edit.submitFailureDetail", { message }),
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
  };

  useEffect(() => {
    isSubmitSuccessful && navigate(groupsPath(), { replace: true });
  }, [isSubmitSuccessful, navigate]);

  usePageTitle(
    groupLoading ? t("group.edit.loading") : TITLE_TEMPLATES.groupEdit,
    {
      prefix:
        group?.name ??
        (willCreate ? t("group.edit.newGroupPrefix") : undefined),
    },
  );

  const handleCancel = async () => {
    navigate(-1);
  };

  if (ServerContext.getInstance()?.user?.isSuperuser !== true) {
    throw new ForbiddenError("only admin can edit a group");
  }

  const pageTitle = group?.name ?? t("group.edit.pageTitleNew");
  const pageDescription = willCreate ? undefined : t("group.edit.description");

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={groupsPath()}>
          {t("group.list.pageTitle")}
        </Typography>
        <Typography color="textPrimary">
          {willCreate
            ? t("group.edit.breadcrumbCreate")
            : t("group.edit.breadcrumbEdit")}
        </Typography>
      </AironeBreadcrumbs>
      <PageHeader title={pageTitle} description={pageDescription}>
        <SubmitButton
          name={t("common.save")}
          disabled={!isDirty || !isValid || isSubmitting || isSubmitSuccessful}
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(handleSubmitOnValid)}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <Container>
        <GroupForm
          control={control}
          setValue={setValue}
          groupId={Number(groupId)}
        />
      </Container>
    </Box>
  );
};
