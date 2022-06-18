import { Box, Typography } from "@mui/material";
import React, { FC, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { Loading } from "../components/common/Loading";
import { PageHeader } from "../components/common/PageHeader";
import {
  EditableEntry,
  initializeEditableEntryAttr,
} from "../components/entry/entryForm/EditableEntry";
import { useTypedParams } from "../hooks/useTypedParams";
import { DjangoContext } from "../utils/DjangoContext";

import {
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
  topPath,
} from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { EntryForm } from "components/entry/EntryForm";

export const EditEntryPage: FC = () => {
  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();

  const history = useHistory();

  const [entryInfo, setEntryInfo] = useState<EditableEntry>();
  const [submittable, setSubmittable] = useState<boolean>(true); // FIXME

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
      setEntryInfo({
        name: entry.value.name,
        attrs: initializeEditableEntryAttr(entry.value.attrs),
      });
    }
  }, [entry]);

  const djangoContext = DjangoContext.getInstance();

  const handleSubmit = async () => {
    const updatedAttr = Object.entries(entryInfo.attrs).map(
      ([{}, attrValue]) => {
        switch (attrValue.type) {
          case djangoContext.attrTypeValue.string:
          case djangoContext.attrTypeValue.text:
          case djangoContext.attrTypeValue.date:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asString,
            };

          case djangoContext.attrTypeValue.boolean:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asBoolean,
            };

          case djangoContext.attrTypeValue.object:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asObject.id ?? "",
            };

          case djangoContext.attrTypeValue.group:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asGroup.id,
            };

          case djangoContext.attrTypeValue.named_object:
            return {
              id: attrValue.schema.id,
              value: {
                id: Object.values(attrValue.value.asNamedObject)[0]?.id,
                name: Object.keys(attrValue.value.asNamedObject)[0],
              },
            };

          case djangoContext.attrTypeValue.array_string:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asArrayString,
            };

          case djangoContext.attrTypeValue.array_object:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asArrayObject.map((x) => x.id),
            };

          case djangoContext.attrTypeValue.array_group:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asArrayGroup.map((x) => x.id),
            };

          case djangoContext.attrTypeValue.array_named_object:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asArrayNamedObject.map((x) => {
                return {
                  id: Object.values(x)[0]?.id,
                  name: Object.keys(x)[0],
                };
              }),
            };
        }
      }
    );

    if (entryId == undefined) {
      await aironeApiClientV2.createEntry(
        entityId,
        entryInfo.name,
        updatedAttr
      );
      history.push(entityEntriesPath(entityId));
    } else {
      await aironeApiClientV2.updateEntry(entryId, entryInfo.name, updatedAttr);
      history.go(0);
    }
  };

  const handleCancel = () => {
    history.replace(entryDetailsPath(entityId, entryId));
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
          <Typography component={Link} to={entityEntriesPath(entity.value.id)}>
            {entity.value.name}
          </Typography>
        )}
        {entry.value && (
          <Typography
            component={Link}
            to={entryDetailsPath(entry.value.schema.id, entry.value.id)}
          >
            {entry.value.name}
          </Typography>
        )}
        <Typography color="textPrimary">編集</Typography>
      </AironeBreadcrumbs>

      <PageHeader
        isSubmittable={submittable}
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
      >
        {entry?.value != null ? (
          <Box display="flex" alignItems="flex-end">
            <Typography variant="h2" mr="32px">
              {entry.value.name}
            </Typography>
            <Typography variant="h4">エントリ編集</Typography>
          </Box>
        ) : (
          <Typography variant="h2">新規エントリの作成</Typography>
        )}
      </PageHeader>

      <Box sx={{ marginTop: "111px", paddingLeft: "10%", paddingRight: "10%" }}>
        {entryInfo && (
          <EntryForm entryInfo={entryInfo} setEntryInfo={setEntryInfo} />
        )}
      </Box>
    </Box>
  );
};
