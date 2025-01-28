import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Container, Typography } from "@mui/material";
import React, { FC, useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { Schema, schema } from "components/role/roleForm/RoleFormSchema";
import { useFormNotification } from "hooks/useFormNotification";
import { usePrompt } from "hooks/usePrompt";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { listCategoryPath, rolesPath, topPath } from "routes/Routes";

export const CategoryEditPage: FC = () => {
  const { categoryId } = useTypedParams<{ categoryId?: number }>();
  const willCreate = categoryId == null;

  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification("カテゴリ", willCreate);

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

  const category = useAsyncWithThrow(async () => {
    return categoryId != null ? await aironeApiClient.getCategory(categoryId) : undefined;
  }, [categoryId]);

  useEffect(() => {
    !category.loading && category.value != null && reset(category.value);
  }, [category.loading]);

  useEffect(() => {
    isSubmitSuccessful && navigate(rolesPath());
  }, [isSubmitSuccessful]);

  const handleSubmitOnValid = useCallback(
    async (category: Schema) => {
      /*
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
            }
          );
        } else {
          enqueueSubmitResult(false);
        }
      }
      */
    },
    [categoryId]
  );

  const handleCancel = async () => {
    navigate(-1);
  };

  if (category.loading) {
    return <Loading />;
  }

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={listCategoryPath()}>
          カテゴリ一覧
        </Typography>
        <Typography color="textPrimary">カテゴリ編集</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={category.value != null ? category.value.name : "新規カテゴリの作成"}
        description={category.value != null ? "カテゴリ編集" : undefined}
      >
        <SubmitButton
          name="保存"
          disabled={
            !isDirty ||
            !isValid ||
            isSubmitting ||
            isSubmitSuccessful
            //category.value?. === false
          }
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(handleSubmitOnValid)}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <Container>
        {/*
          <RoleForm control={control} setValue={setValue} />
        */
        }
      </Container>
    </Box>
  );
};
