import { zodResolver } from "@hookform/resolvers/zod/dist/zod";
import { Box, Container, Typography } from "@mui/material";
import React, { FC, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { GroupForm } from "components/group/GroupForm";
import { schema, Schema } from "components/group/groupForm/GroupFormSchema";
import { useFormNotification } from "hooks/useFormNotification";
import { usePrompt } from "hooks/usePrompt";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { groupsPath, topPath } from "routes/Routes";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";
import { ForbiddenError } from "services/Exceptions";
import { ServerContext } from "services/ServerContext";

export const GroupEditPage: FC = () => {
  const { groupId } = useTypedParams<{ groupId?: number }>();
  const willCreate = groupId == null;

  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification("グループ", willCreate);

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
    "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
  );

  const group = useAsyncWithThrow(async () => {
    return groupId != null
      ? await aironeApiClient.getGroup(groupId)
      : undefined;
  }, [groupId]);

  useEffect(() => {
    !group.loading && group.value != null && reset(group.value);
  }, [group.value]);

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
          (message) => enqueueSubmitResult(false, `詳細: "${message}"`),
          (name, message) => {
            setError(name, { type: "custom", message: message });
            enqueueSubmitResult(false);
          }
        );
      } else {
        enqueueSubmitResult(false);
      }
    }
  };

  useEffect(() => {
    isSubmitSuccessful && navigate(groupsPath(), { replace: true });
  }, [isSubmitSuccessful]);

  const handleCancel = async () => {
    navigate(-1);
  };

  if (ServerContext.getInstance()?.user?.isSuperuser !== true) {
    throw new ForbiddenError("only admin can edit a group");
  }

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={groupsPath()}>
          グループ管理
        </Typography>
        <Typography color="textPrimary">グループ編集</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={group.value?.name ?? "新規グループの作成"}
        description={group.value?.id != 0 ? "グループ編集" : undefined}
      >
        <SubmitButton
          name="保存"
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
