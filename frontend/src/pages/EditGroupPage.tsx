import { zodResolver } from "@hookform/resolvers/zod/dist/zod";
import { Box, Container, Typography } from "@mui/material";
import React, { FC, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, Prompt, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { PageHeader } from "../components/common/PageHeader";
import { schema, Schema } from "../components/group/GroupFormSchema";
import { useFormNotification } from "../hooks/useFormNotification";
import { useTypedParams } from "../hooks/useTypedParams";
import { ExtractAPIException } from "../services/AironeAPIErrorUtil";
import { DjangoContext } from "../services/DjangoContext";
import { ForbiddenError } from "../services/Exceptions";

import { groupsPath, topPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { SubmitButton } from "components/common/SubmitButton";
import { GroupForm } from "components/group/GroupForm";

export const EditGroupPage: FC = () => {
  const { groupId } = useTypedParams<{ groupId?: number }>();
  const willCreate = groupId == null;

  const history = useHistory();
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

  const group = useAsync(async () => {
    return groupId != null
      ? await aironeApiClientV2.getGroup(groupId)
      : undefined;
  }, [groupId]);

  useEffect(() => {
    !group.loading && group.value != null && reset(group.value);
  }, [group.value]);

  const handleSubmitOnValid = async (group: Schema) => {
    try {
      if (willCreate) {
        await aironeApiClientV2.createGroup({
          ...group,
          members: group.members.map((member) => member.id),
        });
      } else {
        await aironeApiClientV2.updateGroup(groupId, {
          ...group,
          members: group.members.map((member) => member.id),
        });
      }
      enqueueSubmitResult(true);
    } catch (e) {
      if (e instanceof Response) {
        await ExtractAPIException<Schema>(
          e,
          (message) => enqueueSubmitResult(false, `詳細: "${message}"`),
          (name, message) =>
            setError(name, { type: "custom", message: message })
        );
      } else {
        enqueueSubmitResult(false);
      }
    }
  };

  useEffect(() => {
    isSubmitSuccessful && history.replace(groupsPath());
  }, [isSubmitSuccessful]);

  const handleCancel = async () => {
    history.goBack();
  };

  if (DjangoContext.getInstance()?.user?.isSuperuser !== true) {
    throw new ForbiddenError("only admin can edit a group");
  }

  return (
    <Box>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={groupsPath()}>
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
          disabled={!isValid || isSubmitting || isSubmitSuccessful}
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

      <Prompt
        when={isDirty && !isSubmitSuccessful}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
