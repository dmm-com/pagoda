import LockIcon from "@mui/icons-material/Lock";
import { Box, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { Dispatch, FC, useEffect, useState } from "react";
import { Link, Prompt } from "react-router-dom";
import { useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { Loading } from "../components/common/Loading";
import { PageHeader } from "../components/common/PageHeader";
import { EditableEntry } from "../components/entry/entryForm/EditableEntry";
import { useTypedParams } from "../hooks/useTypedParams";
import { ExtractAPIErrorMessage } from "../services/AironeAPIErrorUtil";

import {
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
  topPath,
} from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { SubmitButton } from "components/common/SubmitButton";
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

  const history = useHistory();

  const { enqueueSnackbar } = useSnackbar();

  const [entryInfo, _setEntryInfo] = useState<EditableEntry>();
  const [submittable, setSubmittable] = useState<boolean>(false); // FIXME
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [edited, setEdited] = useState<boolean>(false);
  const [isAnchorLink, setIsAnchorLink] = useState<boolean>(false);

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

  const setEntryInfo: Dispatch<EditableEntry> = (entryInfo: EditableEntry) => {
    setEdited(true);
    _setEntryInfo(entryInfo);
  };

  const handleSubmit = async () => {
    const updatedAttr = convertAttrsFormatCtoS(entryInfo?.attrs ?? {});

    // TODO something better to notify validation errors
    if (entryInfo?.name == null) {
      throw new Error("name is required");
    }

    if (entryId == undefined) {
      try {
        await aironeApiClientV2.createEntry(
          entityId,
          entryInfo.name,
          updatedAttr
        );
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
        await aironeApiClientV2.updateEntry(
          entryId,
          entryInfo.name,
          updatedAttr
        );
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

  // NOTE: This should be fixed in near future.
  // This unpeaceful impelmentation guarantees moving page after changing state "submitted"
  // by handleSubmit() processing to prevent showing wrong Prompt message.
  useEffect(() => {
    if (submitted) {
      if (entryId == undefined) {
        // The difference of history.push() and history.replace() is
        // - push() : record moving page at browser history stack
        // - replace() : doesn't record moving page at browser history stack
        //   (NOTE: The replace() is reasonable when user push "back" button of browser,
        //          then editing form won't be revealed.
        history.replace(entityEntriesPath(entityId));
      } else {
        history.replace(entryDetailsPath(entityId, entryId));
      }
    }
  }, [submitted]);

  const handleCancel = () => {
    if (entryId != null) {
      history.replace(entryDetailsPath(entityId, entryId));
    } else {
      history.replace(entityEntriesPath(entityId));
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
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        {entity.value && (
          <Box sx={{ display: "flex" }}>
            <Typography
              component={Link}
              to={entityEntriesPath(entity.value.id)}
            >
              {entity.value.name}
            </Typography>
            {!entity.value.isPublic && <LockIcon />}
          </Box>
        )}
        {entry.value && (
          <Box sx={{ display: "flex" }}>
            <Typography
              component={Link}
              to={entryDetailsPath(
                entry.value?.schema?.id ?? 0,
                entry.value.id
              )}
            >
              {entry.value.name}
            </Typography>
            {!entry.value.isPublic && <LockIcon />}
          </Box>
        )}
        <Typography color="textPrimary">
          {entry.value ? "編集" : "作成"}
        </Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={entry?.value != null ? entry.value.name : "新規エントリの作成"}
        description={entry?.value != null ? "エントリ編集" : undefined}
      >
        <SubmitButton
          name="保存"
          disabled={!submittable}
          handleSubmit={handleSubmit}
          handleCancel={handleCancel}
        />
      </PageHeader>

      {entryInfo && (
        <EntryForm
          entryInfo={entryInfo}
          setEntryInfo={setEntryInfo}
          setIsAnchorLink={setIsAnchorLink}
        />
      )}

      <Prompt
        when={edited && !submitted && !isAnchorLink}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
