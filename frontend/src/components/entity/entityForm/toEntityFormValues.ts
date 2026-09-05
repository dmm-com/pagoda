import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";

import { Schema } from "./EntityFormSchema";

/**
 * Convert an API entity payload into the initial value object of
 * EntityFormSchema, filling in defaults for optional fields.
 */
export const toEntityFormValues = (entity: EntityDetail): Schema => ({
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
      refCond: c.refCond ? { id: c.refCond.id, name: c.refCond.name } : null,
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
  deleteChainExcludeEntities: (entity.deleteChainExcludeEntities ?? []).map(
    (e: { id: number; name: string }) => ({
      id: e.id,
      name: e.name,
    }),
  ),
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
      | number[]
      | null
      | undefined,
    isSummarized: attr.isSummarized,
    nameOrder: attr.nameOrder?.toString() ?? "0",
    namePrefix: attr.namePrefix ?? "",
    namePostfix: attr.namePostfix ?? "",
    displayAttr: attr.displayAttr ?? "",
  })),
});
