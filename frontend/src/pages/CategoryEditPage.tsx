import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Typography } from "@mui/material";
import { FC, useCallback, useEffect, useMemo } from "react";
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
import { useFormNotification } from "hooks/useFormNotification";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { usePrompt } from "hooks/usePrompt";
import { useTranslation } from "hooks/useTranslation";
import { useTypedParams } from "hooks/useTypedParams";
import { translate } from "i18n/config";
import { aironeApiClient } from "repository/AironeApiClient";
import { listCategoryPath, topPath } from "routes/Routes";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";

export const CategoryEditPage: FC = () => {
  const { t } = useTranslation();
  const { categoryId } = useTypedParams<{ categoryId?: number }>({
    allowEmpty: true,
  });
  const willCreate = categoryId == null;

  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification(
    t("common.target.category"),
    willCreate,
  );

  const { data: category, isLoading: categoryLoading } = usePagodaSWR(
    categoryId != null ? ["category", categoryId] : null,
    () => aironeApiClient.getCategory(categoryId!),
  );

  // Fill schema-required defaults for optional API fields.
  const initialValues: Schema | undefined = useMemo(
    () =>
      category != null
        ? { ...category, priority: category.priority ?? 0 }
        : undefined,
    [category],
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
    // Sync form values when the fetched category arrives. Dirty fields are
    // kept so a background revalidation does not clobber user edits.
    values: initialValues,
    resetOptions: { keepDirtyValues: true },
  });

  usePrompt(isDirty && !isSubmitSuccessful, t("category.form.confirmLeave"));

  useEffect(() => {
    isSubmitSuccessful && navigate(listCategoryPath());
  }, [isSubmitSuccessful, navigate]);

  const handleSubmitOnValid = useCallback(
    async (category: Schema) => {
      // Note: This might not necessary any more
      category = { ...category, priority: Number(category.priority) };
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
            (message) =>
              enqueueSubmitResult(
                false,
                translate("category.edit.errorDetail", { message }),
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
    [categoryId, enqueueSubmitResult, setError, willCreate],
  );

  const handleCancel = async () => {
    navigate(-1);
  };

  if (categoryLoading) {
    return <Loading />;
  }

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={listCategoryPath()}>
          {t("category.list.title")}
        </Typography>
        <Typography color="textPrimary">
          {t("category.edit.breadcrumb")}
        </Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={
          category != null ? category.name : t("category.edit.createTitle")
        }
        description={
          category != null ? t("category.edit.breadcrumb") : undefined
        }
      >
        <SubmitButton
          name={t("common.save")}
          disabled={
            !isDirty || !isValid || isSubmitting || isSubmitSuccessful
            //category?. === false
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
