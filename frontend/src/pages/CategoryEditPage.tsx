import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Typography } from "@mui/material";
import React, { FC, useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { AironeLink } from "components";
import { CategoryForm } from "components/category/CategoryForm";
import {
  Schema,
  schema,
} from "components/category/categoryForm/CategoryFormSchema";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { useFormNotification } from "hooks/useFormNotification";
import { usePrompt } from "hooks/usePrompt";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { listCategoryPath, topPath } from "routes/Routes";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";

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
    return categoryId != null
      ? await aironeApiClient.getCategory(categoryId)
      : undefined;
  }, [categoryId]);

  useEffect(() => {
    !category.loading && category.value != null && reset(category.value);
  }, [category.loading]);

  useEffect(() => {
    isSubmitSuccessful && navigate(listCategoryPath());
  }, [isSubmitSuccessful]);

  const handleSubmitOnValid = useCallback(
    async (category: Schema) => {
      try {
        if (willCreate) {
          await aironeApiClient.createCategory(category);
        } else {
          await aironeApiClient.updateCategory(categoryId, category);
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
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={listCategoryPath()}>
          カテゴリ一覧
        </Typography>
        <Typography color="textPrimary">カテゴリ編集</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={
          category.value != null ? category.value.name : "新規カテゴリの作成"
        }
        description={category.value != null ? "カテゴリ編集" : undefined}
      >
        <SubmitButton
          name="保存"
          disabled={
            !isDirty || !isValid || isSubmitting || isSubmitSuccessful
            //category.value?. === false
          }
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(handleSubmitOnValid)}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <CategoryForm control={control} setValue={setValue} />
    </Box>
  );
};
