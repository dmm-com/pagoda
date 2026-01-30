import { WebhookCreateUpdate } from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { Box } from "@mui/material";
import { FC, useEffect } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntityForm } from "components/entity/EntityForm";
import { Schema, schema } from "components/entity/entityForm/EntityFormSchema";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { useFormNotification } from "hooks/useFormNotification";
import { usePageTitle } from "hooks/usePageTitle";
import { usePrompt } from "hooks/usePrompt";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { entitiesPath, entityEntriesPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";
import { BaseAttributeTypes } from "services/Constants";

export const EntityEditPage: FC = () => {
  const { entityId } = useTypedParams<{
    entityId?: number;
  }>({ allowEmpty: true });

  const willCreate = entityId === undefined;

  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification("モデル", willCreate);

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

  const entity = useAsyncWithThrow(async () => {
    if (entityId !== undefined) {
      return await aironeApiClient.getEntity(entityId);
    } else {
      return undefined;
    }
  }, []);

  const referralEntities = useAsyncWithThrow(async () => {
    const entities = await aironeApiClient.getEntities();
    return entities.results;
  });

  const handleCancel = () => {
    if (entityId !== undefined) {
      navigate(entityEntriesPath(entityId), { replace: true });
    } else {
      navigate(entitiesPath(), { replace: true });
    }
  };

  const handleSubmitOnValid = async (entityForm: Schema) => {
    // Adjusted attributes for the API
    const attrs = entityForm.attrs
      .filter((attr) => attr.isWritable)
      .map((attr, index) => {
        // Convert defaultValue to appropriate type
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let processedDefaultValue: any | null = null;
        if (attr.defaultValue != null) {
          if (attr.type === BaseAttributeTypes.number) {
            const numValue = Number(attr.defaultValue);
            if (!isNaN(numValue)) {
              processedDefaultValue = numValue;
            }
          } else if (attr.type === BaseAttributeTypes.bool) {
            processedDefaultValue = Boolean(attr.defaultValue);
          } else if (
            attr.type === BaseAttributeTypes.string ||
            attr.type === BaseAttributeTypes.text
          ) {
            processedDefaultValue = String(attr.defaultValue);
          } else {
            processedDefaultValue = attr.defaultValue;
          }
        }

        return {
          id: attr.id,
          name: attr.name,
          type: attr.type,
          index: index,
          isMandatory: attr.isMandatory,
          isDeleteInChain: attr.isDeleteInChain,
          isSummarized: attr.isSummarized,
          referral: attr.referral.map((r) => r.id),
          isDeleted: false,
          note: attr.note,
          defaultValue: processedDefaultValue,
          nameOrder: Number(attr.nameOrder),
          namePrefix: attr.namePrefix,
          namePostfix: attr.namePostfix,
        };
      });

    const deletedAttrs =
      entity.value?.attrs
        .filter(
          (attr) =>
            !entityForm.attrs.some((attrForm) => attrForm.id === attr.id),
        )
        .map((attr) => ({
          id: attr.id,
          isDeleted: true,
        })) ?? [];

    const webhooks =
      entityForm.webhooks.map(
        (webhook): WebhookCreateUpdate => ({
          id: webhook.id,
          url: webhook.url,
          label: webhook.label,
          isEnabled: webhook.isEnabled,
          isVerified: false,
          headers: webhook.headers,
          isDeleted: false,
        }),
      ) ?? [];

    const deletedWebhooks =
      entity.value?.webhooks
        .filter(
          (webhook) =>
            !entityForm.webhooks.some(
              (webhookForm) => webhookForm.id === webhook.id,
            ),
        )
        .map((webhook) => ({
          id: webhook.id,
          isVerified: false,
          isDeleted: true,
        })) ?? [];

    try {
      if (willCreate) {
        await aironeApiClient.createEntity(
          entityForm.name,
          entityForm.note,
          entityForm.itemNamePattern,
          entityForm.isToplevel,
          attrs,
          webhooks,
        );
      } else {
        await aironeApiClient.updateEntity(
          entityId,
          entityForm.name,
          entityForm.note,
          entityForm.itemNamePattern,
          entityForm.isToplevel,
          [...attrs, ...deletedAttrs],
          [...webhooks, ...deletedWebhooks],
        );
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
  };

  usePageTitle(
    entity.loading || (entityId && entity.loading)
      ? "読み込み中..."
      : TITLE_TEMPLATES.entityEdit,
    {
      prefix: entity.value?.name ?? (entityId == null ? "新規作成" : undefined),
    },
  );

  useEffect(() => {
    if (!entity.loading && entity.value != null) {
      // Convert entity data to form schema format, ensuring defaultValue is included
      const formData: Schema = {
        name: entity.value.name,
        note: entity.value.note ?? "",
        itemNamePattern: entity.value.itemNamePattern ?? "",
        isToplevel: entity.value.isToplevel,
        webhooks: entity.value.webhooks.map((webhook) => ({
          ...webhook,
          url: webhook.url ?? "",
          label: webhook.label ?? "",
          isEnabled: webhook.isEnabled ?? false,
          headers: webhook.headers ?? [],
        })),
        attrs: entity.value.attrs.map((attr) => ({
          ...attr,
          name: attr.name ?? "",
          note: attr.note ?? "",
          referral: (attr.referral ?? []).map((ref) => ({
            id: ref.id,
            name: ref.name,
          })),
          defaultValue: attr.defaultValue as
            | string
            | number
            | boolean
            | null
            | undefined,
          isSummarized: attr.isSummarized,
          nameOrder: attr.nameOrder?.toString() ?? "0",
          namePrefix: attr.namePrefix ?? "",
          namePostfix: attr.namePostfix ?? "",
        })),
      };

      reset(formData);
    }
  }, [entity.loading]);

  useEffect(() => {
    if (isSubmitSuccessful) {
      if (entityId === undefined) {
        navigate(entitiesPath(), { replace: true });
      } else {
        navigate(entityEntriesPath(entityId), { replace: true });
      }
    }
  }, [isSubmitSuccessful]);

  if (entity.loading || referralEntities.loading) {
    return <Loading />;
  }

  return (
    <Box>
      {entityId ? (
        <EntityBreadcrumbs entity={entity.value} title="編集" />
      ) : (
        <EntityBreadcrumbs title="作成" />
      )}

      <PageHeader
        title={entity?.value != null ? entity.value.name : "新規モデルの作成"}
        description={entity?.value && "エンティテイティ詳細 / 編集"}
        targetId={entity.value?.id}
        hasOngoingProcess={entity?.value?.hasOngoingChanges}
      >
        <SubmitButton
          name="保存"
          disabled={!isDirty || !isValid || isSubmitting || isSubmitSuccessful}
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(handleSubmitOnValid)}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <EntityForm
        referralEntities={referralEntities.value}
        control={control}
        setValue={setValue}
      />
    </Box>
  );
};
