import { zodResolver } from "@hookform/resolvers/zod";
import { Box } from "@mui/material";
import { FC, useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
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
import { useIdParams } from "hooks/useIdParams";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { usePrompt } from "hooks/usePrompt";
import { useTranslation } from "hooks/useTranslation";
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
  const { entityId, entryId } = useIdParams({
    required: ["entityId"],
    optional: ["entryId"],
  });

  const willCreate = entryId == null;

  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSubmitResult } = useFormNotification(
    t("common.target.entry"),
    willCreate,
  );

  const {
    formState: { isValid, isDirty, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    reset,
    getValues,
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
    { refreshInterval: 15_000 },
  );

  const { data: entry, isLoading: entryLoading } = usePagodaSWR(
    entryId != undefined ? ["entry", entryId] : null,
    entryId != undefined ? () => aironeApiClient.getEntry(entryId) : null,
    { refreshInterval: 15_000 },
  );

  // Whether the entity/entry needed to build the form have been loaded.
  const initialized = willCreate
    ? !entityLoading && entity != null
    : !entityLoading && entity != null && !entryLoading && entry != null;

  // Whether the loaded entity/entry have been applied to the form. `schema` is
  // only set by `reset` (no field registers it), so it tells a form that has
  // received the loaded data apart from an empty one. The form fields are not
  // rendered before that: array fields would otherwise add placeholder rows,
  // marking the form dirty with values the first reset must not keep.
  const isFormLoaded = useWatch({ control, name: "schema" }) != null;

  useEffect(() => {
    if (!initialized || entity == null) {
      return;
    }
    const entryInfo = formalizeEntryInfo(
      willCreate ? undefined : entry,
      entity,
      excludeAttrs,
    );
    // Read the form state instead of tracking the first load in a ref, so
    // that StrictMode running this effect twice gives the same result.
    if (getValues("schema") == null) {
      if (willCreate) {
        entryInfo.name = useUUID ? crypto.randomUUID() : "";
      }
      reset(entryInfo);
      return;
    }
    // Background refreshes keep the user's local edits.
    if (willCreate) {
      entryInfo.name = getValues("name");
    }
    reset(entryInfo, { keepDirtyValues: true });
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
    if (isFormLoaded) {
      trigger();
    }
  }, [isFormLoaded, trigger]);

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
        targetId={entryId ?? entityId}
        targetKind={entryId != null ? "item" : "model"}
        hasOngoingProcess={
          entry?.hasOngoingChanges ?? (willCreate && entity?.hasOngoingChanges)
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

      {isFormLoaded && entity != null && (
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
