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
import { useFormNotification } from "hooks/useFormNotification";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
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

  const { data: entity, isLoading: entityLoading } = usePagodaSWR(
    entityId !== undefined ? ["entity", entityId] : null,
    () => aironeApiClient.getEntity(entityId!),
  );

  const { data: referralEntities, isLoading: referralEntitiesLoading } =
    usePagodaSWR(["entities"], async () => {
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
      entity?.attrs
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
      entity?.webhooks
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

    const isolationRules = entityForm.isolationRules.map((rule) => ({
      id: rule.id,
      isDeleted: false,
      conditions: rule.conditions.map((c) => ({
        id: c.id,
        attrId: c.attr.id,
        strCond: c.strCond ?? undefined,
        refCondId: c.refCond?.id ?? undefined,
        boolCond: c.boolCond,
        isUnmatch: c.isUnmatch,
      })),
      action: {
        id: rule.action.id,
        isPreventAll: rule.action.isPreventAll,
        preventFromId: rule.action.preventFrom?.id ?? null,
      },
    }));

    const deletedIsolationRules =
      (entity?.isolationRules ?? [])
        .filter(
          (rule) => !entityForm.isolationRules.some((f) => f.id === rule.id),
        )
        .map((rule) => ({
          id: rule.id,
          isDeleted: true,
          conditions: [],
          action: {},
        })) ?? [];

    try {
      const deleteChainExcludeEntityIds =
        entityForm.deleteChainExcludeEntities.map((e) => e.id);

      if (willCreate) {
        await aironeApiClient.createEntity(
          entityForm.name,
          entityForm.note,
          entityForm.itemNamePattern,
          entityForm.itemNameType,
          entityForm.isToplevel,
          attrs,
          webhooks,
          isolationRules,
          deleteChainExcludeEntityIds,
        );
      } else {
        await aironeApiClient.updateEntity(
          entityId,
          entityForm.name,
          entityForm.note,
          entityForm.itemNamePattern,
          entityForm.itemNameType,
          entityForm.isToplevel,
          [...attrs, ...deletedAttrs],
          [...webhooks, ...deletedWebhooks],
          [...isolationRules, ...deletedIsolationRules],
          deleteChainExcludeEntityIds,
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

  usePageTitle(entityLoading ? "読み込み中..." : TITLE_TEMPLATES.entityEdit, {
    prefix: entity?.name ?? (entityId == null ? "新規作成" : undefined),
  });

  useEffect(() => {
    if (!entityLoading && entity != null) {
      // Convert entity data to form schema format, ensuring defaultValue is included
      const formData: Schema = {
        name: entity.name,
        note: entity.note ?? "",
        itemNamePattern: entity.itemNamePattern ?? "",
        itemNameType: entity.itemNameType ?? "US",
        isToplevel: entity.isToplevel,
        isolationRules: entity.isolationRules.map((rule) => ({
          ...rule,
          conditions: rule.conditions.map((c) => ({
            attr: {
              id: c.attr.id,
              name: c.attr.name,
              type: c.attr.type ?? 0,
            },
            strCond: c.strCond ?? null,
            refCond: c.refCond
              ? { id: c.refCond.id, name: c.refCond.name }
              : null,
            boolCond: c.boolCond ?? false,
            isUnmatch: c.isUnmatch ?? false,
          })),
          action: {
            isPreventAll: rule.action?.isPreventAll ?? false,
            preventFrom: rule.action?.preventFrom ?? null,
          },
        })),
        webhooks: entity.webhooks.map((webhook) => ({
          ...webhook,
          url: webhook.url ?? "",
          label: webhook.label ?? "",
          isEnabled: webhook.isEnabled ?? false,
          headers: webhook.headers ?? [],
        })),
        deleteChainExcludeEntities: (
          entity.deleteChainExcludeEntities ?? []
        ).map((e: { id: number; name: string }) => ({
          id: e.id,
          name: e.name,
        })),
        attrs: entity.attrs.map((attr) => ({
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
  }, [entity, entityLoading, reset]);

  useEffect(() => {
    if (isSubmitSuccessful) {
      if (entityId === undefined) {
        navigate(entitiesPath(), { replace: true });
      } else {
        navigate(entityEntriesPath(entityId), { replace: true });
      }
    }
  }, [isSubmitSuccessful]);

  if (entityLoading || referralEntitiesLoading) {
    return <Loading />;
  }

  return (
    <Box>
      {entityId ? (
        <EntityBreadcrumbs entity={entity} title="編集" />
      ) : (
        <EntityBreadcrumbs title="作成" />
      )}

      <PageHeader
        title={entity != null ? entity.name : "新規モデルの作成"}
        description={entity && "エンティテイティ詳細 / 編集"}
        targetId={entity?.id}
        hasOngoingProcess={entity?.hasOngoingChanges}
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
        referralEntities={referralEntities}
        control={control}
        setValue={setValue}
      />
    </Box>
  );
};
