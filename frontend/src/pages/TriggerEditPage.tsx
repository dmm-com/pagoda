import {
  EntryAttributeTypeTypeEnum,
  TriggerParentUpdate,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Autocomplete,
  Box,
  Container,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useCallback, useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Prompt, useHistory } from "react-router-dom";

import { triggersPath } from "Routes";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { ActionForm } from "components/trigger/ActionForm";
import { Conditions } from "components/trigger/Conditions";
import { Schema, schema } from "components/trigger/TriggerFormSchema";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { useFormNotification } from "hooks/useFormNotification";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

const StyledFlexColumnBox = styled(Box)({
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  marginBottom: "48px",
});

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
  color: "#FFFFFF",
  boxSizing: "border-box",
}));

const StyledTableBody = styled(TableBody)({
  "tr:nth-of-type(odd)": {
    backgroundColor: "white",
  },
  "tr:nth-of-type(even)": {
    backgroundColor: "#607D8B0A",
  },
  "& td": {
    padding: "8px",
  },
});

export const TriggerEditPage: FC = () => {
  const { triggerId } = useTypedParams<{ triggerId: number }>();
  const willCreate = triggerId === undefined;

  const history = useHistory();
  const { enqueueSubmitResult } = useFormNotification("トリガー", willCreate);

  const actionTrigger = useAsyncWithThrow(async () => {
    if (triggerId !== undefined) {
      // set valid for actionTrigger context when opening edit page
      return await aironeApiClient.getTrigger(triggerId);
    } else {
      return undefined;
    }
  }, []);

  const {
    formState: { isDirty, isValid, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    reset,
    setError,
    setValue,
    getValues,
    trigger,
    control,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onBlur",
    defaultValues: {
      id: 0,
    },
  });

  const entities = useAsyncWithThrow(async () => {
    const entities = await aironeApiClient.getEntities();
    return entities.results;
  });

  const [entityId, setEntityId] = useState<number>();
  const entity = useAsyncWithThrow(async () => {
    if (entityId) {
      return await aironeApiClient.getEntity(entityId);
    } else {
      return undefined;
    }
  }, [entityId]);

  const convertConditions2ServerFormat = (trigger: Schema) => {
    if (!entity.value) {
      return [];
    }

    return trigger.conditions.map((cond) => {
      const attrInfo = entity.value?.attrs.find(
        (attr) => attr.id === cond.attr.id
      );

      switch (attrInfo?.type) {
        case EntryAttributeTypeTypeEnum.STRING:
        case EntryAttributeTypeTypeEnum.ARRAY_STRING:
          return { attrId: cond.attr.id, cond: cond.strCond ?? "" };

        case EntryAttributeTypeTypeEnum.BOOLEAN:
          return { attrId: cond.attr.id, cond: String(cond.boolCond) };

        case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
        case EntryAttributeTypeTypeEnum.OBJECT:
          return { attrId: cond.attr.id, cond: String(cond.refCond?.id ?? 0) };
        default:
          return { attrId: cond.attr.id, cond: "" };
      }
    });
  };
  const convertActions2ServerFormat = (trigger: Schema) => {
    if (!entity.value) {
      return [];
    }

    const retValues: any[] = [];
    trigger.actions.forEach((action) => {
      const attrInfo = entity.value?.attrs.find(
        (attr) => attr.id === action.attr.id
      );
      switch (attrInfo?.type) {
        case EntryAttributeTypeTypeEnum.STRING:
          action.values.map((val) => {
            retValues.push({
              attrId: action.attr.id,
              value: val.strCond ?? "",
            });
          });
          break;

        case EntryAttributeTypeTypeEnum.ARRAY_STRING:
          retValues.push({
            attrId: action.attr.id,
            values: action.values.map((val) => val.strCond ?? ""),
          });
          break;

        case EntryAttributeTypeTypeEnum.BOOLEAN:
          action.values.map((val) => {
            retValues.push({
              attrId: action.attr.id,
              value: String(val.boolCond),
            });
          });
          break;

        case EntryAttributeTypeTypeEnum.OBJECT:
          action.values.map((val) => {
            retValues.push({
              attrId: action.attr.id,
              value: String(val.refCond?.id ?? 0),
            });
          });
          break;

        case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
          console.log(
            "[onix/EntryAttributeTypeTypeEnum.NAMED_OBJECT] attr: ",
            action.attr
          );
          console.log(
            "[onix/EntryAttributeTypeTypeEnum.NAMED_OBJECT] values: ",
            action.values
          );
          action.values.map((val) => {
            retValues.push({
              attrId: action.attr.id,
              value: {
                name: val.strCond,
                id: val.refCond?.id ?? 0,
              },
            });
          });
          break;

        case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
          retValues.push({
            attrId: action.attr.id,
            values: action.values
              .filter((val) => val.refCond && val.refCond?.id > 0)
              .map((val) => val.refCond?.id ?? 0),
          });
          break;

        case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
          console.log("action", action);
          retValues.push({
            attrId: action.attr.id,
            values: action.values.map((val) => ({
              name: val.strCond,
              id: val.refCond?.id ?? 0,
            })),
          });
          break;
      }
    });

    console.log("[onix/convertConditions2ServerFormat] retValues: ", retValues);

    return retValues;
  };

  const handleSubmitOnValid = useCallback(
    async (trigger: Schema) => {
      const triggerCreateUpdate: TriggerParentUpdate = {
        id: triggerId,
        entityId: trigger.entity.id,
        conditions: convertConditions2ServerFormat(trigger) ?? [],
        actions: convertActions2ServerFormat(trigger) ?? [],
      };
      try {
        if (triggerId !== undefined) {
          await aironeApiClient.updateTrigger(triggerId, triggerCreateUpdate);
          enqueueSubmitResult(true);
        } else {
          await aironeApiClient.createTrigger(triggerCreateUpdate);
          enqueueSubmitResult(true);
        }
      } catch (e) {
        const errMsg = "Failed to submit trigger";

        enqueueSubmitResult(false, errMsg);
        setError("conditions", { message: errMsg });
      }
    },
    [triggerId, entity]
  );

  const handleCancel = async () => {
    history.goBack();
  };

  useEffect(() => {
    if (!actionTrigger.loading && actionTrigger.value != null) {
      // set defult value to React-hook-form
      reset(actionTrigger.value);

      setEntityId(actionTrigger.value.entity.id);

      trigger();
    }
  }, [actionTrigger.loading]);

  useEffect(() => {
    if (entity.value && entity.value.id !== 0) {
      setValue(
        `entity`,
        {
          id: entity.value.id,
          name: entity.value.name,
        },
        {
          shouldValidate: true,
        }
      );
    }
    trigger();
  }, [entity.loading]);

  useEffect(() => {
    if (isSubmitSuccessful) {
      history.replace(triggersPath());
    }
  }, [isSubmitSuccessful]);

  return (
    <Box>
      {entity.value ? (
        <EntityBreadcrumbs entity={entity.value} title="編集" />
      ) : (
        <EntityBreadcrumbs title="作成" />
      )}

      <PageHeader
        title={
          triggerId && entity.value ? entity.value.name : "新規トリガーの作成"
        }
        description={triggerId ? entity.value && "トリガー編集" : ""}
      >
        <SubmitButton
          name="保存"
          disabled={!isDirty || !isValid || isSubmitting || isSubmitSuccessful}
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(handleSubmitOnValid)}
          handleCancel={handleCancel}
        />
      </PageHeader>

      <Container>
        <StyledFlexColumnBox>
          <Typography variant="h4">設定対象のエンティティ</Typography>

          <Controller
            name={`entity`}
            control={control}
            render={({ field }) => (
              <Autocomplete
                value={field.value ?? null}
                options={entities.value ?? []}
                getOptionLabel={(option: { id: number; name: string }) =>
                  option.name
                }
                isOptionEqualToValue={(option, value) => option.id === value.id}
                disabled={entities.loading}
                onChange={(_, value: { id: number; name: string } | null) => {
                  if (value && value.id != entityId) {
                    // set EntityId to state variable
                    setEntityId(value.id);

                    // reset Entity information of React-hook-form
                    const triggerInfo = getValues();

                    // reset whole information conditions and actions because of changing Entity
                    reset({
                      ...triggerInfo,
                      entity: value,
                      conditions: [],
                      actions: [],
                    });

                    /*
                    setValue(`entity`, value, {
                      shouldDirty: true,
                      shouldValidate: true,
                    });
                    */
                  }
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="outlined"
                    placeholder="エンティティを選択"
                  />
                )}
                fullWidth
              />
            )}
          />
        </StyledFlexColumnBox>

        {/* Trigger configuration forms should be shown after target entity is defined */}
        {entity.value && (
          <>
            <StyledFlexColumnBox>
              <Typography variant="h4" align="center" my="32px">
                条件
              </Typography>
              <Table>
                <TableHead>
                  <HeaderTableRow>
                    <HeaderTableCell width="400px">属性名</HeaderTableCell>
                    <HeaderTableCell width="400px">値</HeaderTableCell>
                    <HeaderTableCell width="100px">削除</HeaderTableCell>
                    <HeaderTableCell width="100px">追加</HeaderTableCell>
                  </HeaderTableRow>
                </TableHead>
                <StyledTableBody>
                  {entity.value && (
                    <Conditions control={control} entity={entity.value} />
                  )}
                </StyledTableBody>
              </Table>
            </StyledFlexColumnBox>

            <StyledFlexColumnBox>
              <Typography variant="h4" align="center" my="32px">
                アクション
              </Typography>
              <Table>
                <TableHead>
                  <HeaderTableRow>
                    <HeaderTableCell width="400px">属性名</HeaderTableCell>
                    <HeaderTableCell width="400px">値</HeaderTableCell>
                    <HeaderTableCell width="100px">削除</HeaderTableCell>
                    <HeaderTableCell width="100px">追加</HeaderTableCell>
                  </HeaderTableRow>
                </TableHead>
                <StyledTableBody>
                  {entity.value && (
                    <ActionForm
                      control={control}
                      entity={entity.value}
                      resetActionValues={(index: number) => {
                        setValue(
                          `actions.${index}.values`,
                          [
                            {
                              id: 0,
                              strCond: "",
                              refCond: null,
                            },
                          ],
                          {
                            shouldDirty: true,
                            shouldValidate: true,
                          }
                        );
                      }}
                    />
                  )}
                </StyledTableBody>
              </Table>
            </StyledFlexColumnBox>
          </>
        )}
      </Container>
      <Prompt
        when={isDirty && !isSubmitSuccessful}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
    </Box>
  );
};
