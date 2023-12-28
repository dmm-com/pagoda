import { zodResolver } from "@hookform/resolvers/zod";
import { Box } from "@mui/material";
import React, { FC, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Prompt } from "react-router-dom";
import { useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { entityEntriesPath, entryDetailsPath } from "Routes";
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
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";
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
}

export const EntryEditPage: FC<Props> = ({
  excludeAttrs = [],
  EntryForm = DefaultEntryForm,
}) => {
  const { entityId, entryId } = useTypedParams<{
    entityId: number;
    entryId: number;
  }>();

  const willCreate = entryId == null;

  const history = useHistory();
  const { enqueueSubmitResult } = useFormNotification("エントリ", willCreate);

  const [initialized, setInitialized] = useState(false);

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

  const entity = useAsync(async () => {
    return await aironeApiClientV2.getEntity(entityId);
  });

  const entry = useAsync(async () => {
    return entryId != undefined
      ? await aironeApiClientV2.getEntry(entryId)
      : undefined;
  });

  useEffect(() => {
    if (willCreate) {
      if (!entity.loading && entity.value != null) {
        const entryInfo = formalizeEntryInfo(
          undefined,
          entity.value,
          excludeAttrs
        );
        reset(entryInfo);
        setInitialized(true);
      }
    } else {
      if (
        !entity.loading &&
        entity.value != null &&
        !entry.loading &&
        entry.value != null
      ) {
        const entryInfo = formalizeEntryInfo(
          entry.value,
          entity.value,
          excludeAttrs
        );
        reset(entryInfo);
        setInitialized(true);
      }
    }
  }, [willCreate, entity.value, entry.value]);

  useEffect(() => {
    if (isSubmitSuccessful) {
      if (willCreate) {
        history.replace(entityEntriesPath(entityId));
      } else {
        history.replace(entryDetailsPath(entityId, entryId));
      }
    }
  }, [isSubmitSuccessful]);

  const handleSubmitOnValid = async (entry: Schema) => {
    const updatedAttr = convertAttrsFormatCtoS(entry.attrs);

    try {
      if (willCreate) {
        await aironeApiClientV2.createEntry(entityId, entry.name, updatedAttr);
      } else {
        await aironeApiClientV2.updateEntry(entryId, entry.name, updatedAttr);
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
          }
        );
      } else {
        enqueueSubmitResult(false);
      }
    }
  };

  const handleCancel = () => {
    if (willCreate) {
      history.replace(entityEntriesPath(entityId));
    } else {
      history.replace(entryDetailsPath(entityId, entryId));
    }
  };

  if (entity.loading || entry.loading) {
    return <Loading />;
  }

  if (
    !entity.loading &&
    entity.value == undefined &&
    !entry.loading &&
    entry.value == undefined
  ) {
    throw Error("both entity and entry are invalid");
  }

  return (
    <Box>
      {entry.value ? (
        <EntryBreadcrumbs entry={entry.value} title="編集" />
      ) : (
        <EntityBreadcrumbs entity={entity.value} title="作成" />
      )}

      <PageHeader
        title={entry?.value != null ? entry.value.name : "新規エントリの作成"}
        description={entry?.value != null ? "エントリ編集" : undefined}
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

      {initialized && entity.value != null && (
        <EntryForm
          entity={{
            ...entity.value,
            attrs: entity.value.attrs.filter(
              (attr) => !excludeAttrs.includes(attr.name)
            ),
          }}
          control={control}
          setValue={setValue}
        />
      )}

      <Prompt
        when={isDirty && !isSubmitSuccessful}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
