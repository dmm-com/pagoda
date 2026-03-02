import { zodResolver } from "@hookform/resolvers/zod";
import { Box } from "@mui/material";
import { FC, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { v4 as uuidv4 } from "uuid";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import {
  EntryForm as DefaultEntryForm,
  EntryFormProps,
} from "components/entry/EntryForm";
import { Schema, schema } from "components/entry/entryForm/EntryFormSchema";
import { useFormNotification } from "hooks/useFormNotification";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { usePrompt } from "hooks/usePrompt";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { entityEntriesPath, entryDetailsPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";
import {
  extractAPIException,
  isResponseError,
} from "services/AironeAPIErrorUtil";
import {
  convertAttrsFormatCtoS,
  formalizeEntryInfo,
} from "services/entry/Edit";

interface Props {
  excludeAttrs?: string[];
  EntryForm?: FC<EntryFormProps>;
  useUUID?: boolean;
}

export const EntryEditPage: FC<Props> = ({
  excludeAttrs = [],
  EntryForm = DefaultEntryForm,
  useUUID = false,
}) => {
  const { entityId, entryId } = useTypedParams<{
    entityId: number;
    entryId: number;
  }>();

  const willCreate = entryId == null;

  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification("アイテム", willCreate);

  const [initialized, setInitialized] = useState(false);

  const {
    formState: { isValid, isDirty, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    reset,
    setError,
    setValue,
    control,
    trigger,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onBlur",
  });

  usePrompt(
    isDirty && !isSubmitSuccessful,
    "編集した内容は失われてしまいますが、このページを離れてもよろしいですか？",
  );

  const { data: entity, isLoading: entityLoading } = usePagodaSWR(
    ["entity", entityId],
    () => aironeApiClient.getEntity(entityId),
  );

  const { data: entry, isLoading: entryLoading } = usePagodaSWR(
    entryId != undefined ? ["entry", entryId] : null,
    () => aironeApiClient.getEntry(entryId!),
  );

  useEffect(() => {
    if (willCreate) {
      if (!entityLoading && entity != null) {
        const entryInfo = formalizeEntryInfo(undefined, entity, excludeAttrs);
        entryInfo.name = useUUID ? uuidv4() : "";
        reset(entryInfo);
        setInitialized(true);
      }
    } else {
      if (!entityLoading && entity != null && !entryLoading && entry != null) {
        const entryInfo = formalizeEntryInfo(entry, entity, excludeAttrs);
        reset(entryInfo);
        setInitialized(true);
      }
    }
  }, [willCreate, entity, entry]);

  useEffect(() => {
    if (isSubmitSuccessful) {
      if (willCreate) {
        navigate(entityEntriesPath(entityId), { replace: true });
      } else {
        navigate(entryDetailsPath(entityId, entryId), { replace: true });
      }
    }
  }, [isSubmitSuccessful]);

  // Show the first validation feedback
  useEffect(() => {
    if (initialized) {
      trigger();
    }
  }, [initialized]);

  usePageTitle(
    entityLoading || (entryId && entryLoading)
      ? "読み込み中..."
      : TITLE_TEMPLATES.entryEdit,
    {
      prefix: entry?.name ?? (entryId == null ? "新規作成" : undefined),
    },
  );

  const handleSubmitOnValid = async (entry: Schema) => {
    const updatedAttr = convertAttrsFormatCtoS(entry.attrs);

    try {
      if (willCreate) {
        await aironeApiClient.createEntry(entityId, entry.name, updatedAttr);
      } else {
        await aironeApiClient.updateEntry(entryId, entry.name, updatedAttr);
      }
      enqueueSubmitResult(true);
    } catch (e) {
      console.log("e", e);
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

  const handleCancel = () => {
    if (willCreate) {
      navigate(entityEntriesPath(entityId), { replace: true });
    } else {
      navigate(entryDetailsPath(entityId, entryId), { replace: true });
    }
  };

  if (entityLoading || entryLoading) {
    return <Loading />;
  }

  if (
    !entityLoading &&
    entity == undefined &&
    !entryLoading &&
    entry == undefined
  ) {
    throw Error("both entity and entry are invalid");
  }

  // set Name automatically when itemNameType is not "US" when creating new Item
  const skipItemName = entity?.itemNameType !== "US";
  if (skipItemName && willCreate) {
    setValue("name", crypto.randomUUID());
  }

  return (
    <Box>
      {entry ? (
        <EntryBreadcrumbs entry={entry} title="編集" />
      ) : (
        <EntityBreadcrumbs entity={entity} title="作成" />
      )}

      <PageHeader
        title={entry != null ? entry.name : "新規アイテムの作成"}
        description={entry != null ? "アイテム編集" : undefined}
      >
        <SubmitButton
          name="保存"
          disabled={!isDirty || !isValid || isSubmitting || isSubmitSuccessful}
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(handleSubmitOnValid, (errors) => {
            console.log(errors);
          })}
          handleCancel={handleCancel}
        />
      </PageHeader>

      {initialized && entity != null && (
        <EntryForm
          entity={{
            ...entity,
            attrs: entity.attrs.filter(
              (attr) => !excludeAttrs.includes(attr.name),
            ),
          }}
          control={control}
          setValue={setValue}
          skipItemName={skipItemName}
        />
      )}
    </Box>
  );
};
