import { zodResolver } from "@hookform/resolvers/zod";
import { Box } from "@mui/material";
import { FC, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

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
import { useTranslation } from "hooks/useTranslation";
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

  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification(
    t("common.target.entry"),
    willCreate,
  );

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
    t("entryForm.editPage.leaveConfirm"),
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
        entryInfo.name = useUUID ? crypto.randomUUID() : "";
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
  }, [isSubmitSuccessful, willCreate, entityId, entryId, navigate]);

  // Show the first validation feedback
  useEffect(() => {
    if (initialized) {
      trigger();
    }
  }, [initialized, trigger]);

  usePageTitle(
    entityLoading || (entryId && entryLoading)
      ? t("entryForm.editPage.loading")
      : TITLE_TEMPLATES.entryEdit,
    {
      prefix:
        entry?.name ??
        (entryId == null ? t("entryForm.editPage.newEntry") : undefined),
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
          (message) =>
            enqueueSubmitResult(
              false,
              t("entryForm.editPage.errorDetail", { message }),
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
        <EntryBreadcrumbs
          entry={entry}
          title={t("entryForm.editPage.editBreadcrumb")}
        />
      ) : (
        <EntityBreadcrumbs
          entity={entity}
          title={t("entryForm.editPage.createBreadcrumb")}
        />
      )}

      <PageHeader
        title={
          entry != null ? entry.name : t("entryForm.editPage.newEntryTitle")
        }
        description={
          entry != null ? t("entryForm.editPage.editDescription") : undefined
        }
      >
        <SubmitButton
          name={t("common.save")}
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
