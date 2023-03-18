import { zodResolver } from "@hookform/resolvers/zod";
import { Box } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { Dispatch, FC, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Prompt } from "react-router-dom";
import { useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { Loading } from "../components/common/Loading";
import { PageHeader } from "../components/common/PageHeader";
import { Schema, schema } from "../components/entry/EntryFormSchema";
import { useTypedParams } from "../hooks/useTypedParams";
import { ExtractAPIErrorMessage } from "../services/AironeAPIErrorUtil";

import { entityEntriesPath, entryDetailsPath } from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { SubmitButton } from "components/common/SubmitButton";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { EntryForm } from "components/entry/EntryForm";
import {
  convertAttrsFormatCtoS,
  formalizeEntryInfo,
  initializeEntryInfo,
  isSubmittable,
} from "services/entry/Edit";

interface Props {
  excludeAttrs?: string[];
}

export const EditEntryPage: FC<Props> = ({ excludeAttrs = [] }) => {
  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();

  const willCreate = entryId == null;

  const history = useHistory();

  const { enqueueSnackbar } = useSnackbar();

  const [entryInfo, _setEntryInfo] = useState<Schema>();
  const [submittable, setSubmittable] = useState<boolean>(false); // FIXME
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [edited, setEdited] = useState<boolean>(false);
  const [isAnchorLink, setIsAnchorLink] = useState<boolean>(false);

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
    return entityId != undefined
      ? await aironeApiClientV2.getEntity(entityId)
      : undefined;
  });

  const entry = useAsync(async () => {
    return entryId != undefined
      ? await aironeApiClientV2.getEntry(entryId)
      : undefined;
  });

  useEffect(() => {
    if (!entry.loading && entry.value !== undefined) {
      _setEntryInfo(formalizeEntryInfo(entry.value, excludeAttrs));
    } else if (
      !entry.loading &&
      !entity.loading &&
      entity.value !== undefined
    ) {
      _setEntryInfo(initializeEntryInfo(entity.value));
    }
  }, [entity, entry]);

  useEffect(() => {
    setSubmittable(entryInfo != null && isSubmittable(entryInfo));
  }, [entryInfo]);

  useEffect(() => {
    if (willCreate) {
      if (!entity.loading && entity.value != null) {
        reset(initializeEntryInfo(entity.value));
      }
    } else {
      if (!entry.loading && entry.value != null) {
        reset(formalizeEntryInfo(entry.value, excludeAttrs));
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

  const setEntryInfo: Dispatch<Schema> = (entryInfo: Schema) => {
    setEdited(true);
    _setEntryInfo(entryInfo);
  };

  const handleSubmitOnValid = async (entry: Schema) => {
    const updatedAttr = convertAttrsFormatCtoS(entryInfo?.attrs ?? {});

    if (willCreate) {
      try {
        await aironeApiClientV2.createEntry(entityId, entry.name, updatedAttr);
        setSubmitted(true);
        enqueueSnackbar("エントリの作成が完了しました", {
          variant: "success",
        });
      } catch (e) {
        if (e instanceof Response) {
          if (!e.ok) {
            const json = await e.json();
            const reasons = ExtractAPIErrorMessage(json);

            enqueueSnackbar(`エントリの作成が失敗しました。詳細: ${reasons}`, {
              variant: "error",
            });
          }
        } else {
          throw e;
        }
      }
    } else {
      try {
        await aironeApiClientV2.updateEntry(entryId, entry.name, updatedAttr);
        setSubmitted(true);
        enqueueSnackbar("エントリの更新が完了しました", {
          variant: "success",
        });
      } catch (e) {
        if (e instanceof Response) {
          if (!e.ok) {
            const json = await e.json();
            const reasons = ExtractAPIErrorMessage(json);

            enqueueSnackbar(`エントリの更新が失敗しました。詳細: ${reasons}`, {
              variant: "error",
            });
          }
        } else {
          throw e;
        }
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
          disabled={/*!isValid || */ isSubmitting || isSubmitSuccessful}
          handleSubmit={handleSubmit(handleSubmitOnValid, (errors) => {
            console.log(errors);
          })}
          handleCancel={handleCancel}
        />
      </PageHeader>

      {entryInfo && (
        <EntryForm
          entryInfo={entryInfo}
          setEntryInfo={setEntryInfo}
          setIsAnchorLink={setIsAnchorLink}
          control={control}
        />
      )}

      <Prompt
        when={isDirty && !isSubmitSuccessful && !isAnchorLink}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
