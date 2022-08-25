import AppsIcon from "@mui/icons-material/Apps";
import { Box, Button, IconButton, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { Loading } from "../components/common/Loading";
import { PageHeader } from "../components/common/PageHeader";
import {
  EditableEntry,
  EditableEntryAttrs,
} from "../components/entry/entryForm/EditableEntry";
import { useTypedParams } from "../hooks/useTypedParams";
import { GetReasonFromCode } from "../utils/AironeAPIErrorUtil";
import { DjangoContext } from "../utils/DjangoContext";

import {
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
  topPath,
} from "Routes";
import { aironeApiClientV2 } from "apiclient/AironeApiClientV2";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryForm } from "components/entry/EntryForm";

interface Props {
  excludeAttrs?: string[];
}

export const EditEntryPage: FC<Props> = ({ excludeAttrs = [] }) => {
  const { entityId, entryId } =
    useTypedParams<{ entityId: number; entryId: number }>();

  const history = useHistory();

  const { enqueueSnackbar } = useSnackbar();

  const [entryAnchorEl, setEntryAnchorEl] =
    useState<HTMLButtonElement | null>();
  const [entryInfo, setEntryInfo] = useState<EditableEntry>();
  const [submittable, setSubmittable] = useState<boolean>(false); // FIXME

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

  const djangoContext = DjangoContext.getInstance();

  useEffect(() => {
    if (!entry.loading && entry.value !== undefined) {
      setEntryInfo({
        name: entry.value.name,
        attrs: Object.fromEntries(
          entry.value.attrs
            .filter((attr) => !excludeAttrs.includes(attr.schema.name))
            .map((attr): [string, EditableEntryAttrs] => {
              function getAttrValue(attr) {
                switch (attr.type) {
                  case djangoContext.attrTypeValue.array_string:
                    return attr.value?.asArrayString?.length > 0
                      ? attr.value
                      : { asArrayString: [""] };
                  case djangoContext.attrTypeValue.array_named_object:
                    return attr.value?.asArrayNamedObject?.length > 0
                      ? attr.value
                      : { asArrayNamedObject: [{ "": null }] };
                  default:
                    return attr.value;
                }
              }

              return [
                attr.schema.name,
                {
                  id: attr.id,
                  type: attr.type,
                  isMandatory: attr.isMandatory,
                  schema: attr.schema,
                  value: getAttrValue(attr),
                },
              ];
            })
        ),
      });
    } else if (
      !entry.loading &&
      !entity.loading &&
      entity.value !== undefined
    ) {
      setEntryInfo({
        name: "",
        attrs: Object.fromEntries(
          entity.value.attrs.map((attr): [string, EditableEntryAttrs] => [
            attr.name,
            {
              type: attr.type,
              isMandatory: attr.isMandatory,
              schema: {
                id: attr.id,
                name: attr.name,
              },
              value: {
                asString: "",
                asBoolean: false,
                asObject: null,
                asGroup: null,
                asNamedObject: { "": null },
                asArrayString: [""],
                asArrayObject: [],
                asArrayGroup: [],
                asArrayNamedObject: [{ "": null }],
              },
            },
          ])
        ),
      });
    }
  }, [entity, entry]);

  useEffect(() => {
    if (entryInfo?.name) {
      setSubmittable(
        Object.entries(entryInfo?.attrs ?? {})
          .filter(([{}, attrValue]) => attrValue.isMandatory)
          .map((attr) =>
            [
              attr[1].type === djangoContext.attrTypeValue.boolean,
              attr[1].value.asString !== "",
              attr[1].value.asObject,
              attr[1].value.asGroup,
              Object.keys(attr[1].value.asNamedObject ?? {})[0] &&
                Object.values(attr[1].value.asNamedObject ?? {})[0],
              attr[1].value.asArrayString?.filter((v) => v).length,
              attr[1].value.asArrayObject?.filter((v) => v).length,
              attr[1].value.asArrayGroup?.filter((v) => v).length,
              attr[1].value.asArrayNamedObject?.filter(
                (v) => Object.keys(v)[0] && Object.values(v)[0]
              ).length,
            ].some((value) => value)
          )
          .every((value) => value)
      );
    } else {
      setSubmittable(false);
    }
  }, [entryInfo]);

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
              value: attrValue.value.asObject?.id ?? "",
            };

          case djangoContext.attrTypeValue.group:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asGroup?.id ?? "",
            };

          case djangoContext.attrTypeValue.named_object:
            return {
              id: attrValue.schema.id,
              value: {
                id: Object.values(attrValue.value.asNamedObject)[0]?.id ?? "",
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
              value: attrValue.value.asArrayObject?.map((x) => x.id),
            };

          case djangoContext.attrTypeValue.array_group:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asArrayGroup?.map((x) => x.id),
            };

          case djangoContext.attrTypeValue.array_named_object:
            return {
              id: attrValue.schema.id,
              value: attrValue.value.asArrayNamedObject?.map((x) => {
                return {
                  id: Object.values(x)[0]?.id ?? "",
                  name: Object.keys(x)[0],
                };
              }),
            };
        }
      }
    );

    if (entryId == undefined) {
      try {
        await aironeApiClientV2.createEntry(
          entityId,
          entryInfo.name,
          updatedAttr
        );
        enqueueSnackbar("エントリの作成が完了しました", {
          variant: "success",
        });
        history.push(entityEntriesPath(entityId));
      } catch (e) {
        if (e instanceof Response) {
          if (!e.ok) {
            const json = await e.json();
            let reasons = "";
            if (json["name"]) {
              reasons = json["name"]
                .map((errorInfo) =>
                  GetReasonFromCode(errorInfo["airone_error_code"])
                )
                .join();
            }
            if (json["non_field_errors"]) {
              reasons = json["non_field_errors"]
                .map((errorInfo) =>
                  GetReasonFromCode(errorInfo["airone_error_code"])
                )
                .join();
            }
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
        enqueueSnackbar("エントリの更新が完了しました", {
          variant: "success",
        });
        history.push(entryDetailsPath(entityId, entryId));
      } catch (e) {
        if (e instanceof Response) {
          if (!e.ok) {
            const json = await e.json();
            let reasons = "";
            if (json["name"]) {
              reasons = json["name"]
                .map((errorInfo) =>
                  GetReasonFromCode(errorInfo["airone_error_code"])
                )
                .join();
            }
            if (json["non_field_errors"]) {
              reasons = json["non_field_errors"]
                .map((errorInfo) =>
                  GetReasonFromCode(errorInfo["airone_error_code"])
                )
                .join();
            }
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
        <Typography color="textPrimary">
          {entry.value ? "編集" : "作成"}
        </Typography>
      </AironeBreadcrumbs>

      <PageHeader
        title={entry?.value != null ? entry.value.name : "新規エントリの作成"}
        subTitle={entry?.value != null && "エントリ編集"}
        componentSubmits={
          <Box display="flex" justifyContent="center">
            <Box mx="4px">
              <Button
                variant="contained"
                color="secondary"
                disabled={!submittable}
                onClick={handleSubmit}
              >
                保存
              </Button>
            </Box>
            <Box mx="4px">
              <Button variant="outlined" color="primary" onClick={handleCancel}>
                キャンセル
              </Button>
            </Box>
          </Box>
        }
        componentControl={
          <Box>
            <IconButton
              onClick={(e) => {
                setEntryAnchorEl(e.currentTarget);
              }}
            >
              <AppsIcon />
            </IconButton>
            <EntryControlMenu
              entityId={entityId}
              entryId={entryId}
              anchorElem={entryAnchorEl}
              handleClose={() => setEntryAnchorEl(null)}
            />
          </Box>
        }
      />

      <Box>
        {entryInfo && (
          <EntryForm entryInfo={entryInfo} setEntryInfo={setEntryInfo} />
        )}
      </Box>
    </Box>
  );
};
