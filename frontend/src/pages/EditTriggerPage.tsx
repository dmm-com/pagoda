import { zodResolver } from "@hookform/resolvers/zod";
import {
  Box,
  Container,
  MenuItem,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useCallback } from "react";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import { useHistory } from "react-router-dom";

import { TriggerParentUpdate } from "@dmm-com/airone-apiclient-typescript-fetch";
import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { Schema, schema } from "components/trigger/TriggerFormSchema";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { useFormNotification } from "hooks/useFormNotification";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";

const HeaderTableRow = styled(TableRow)(({ }) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({ }) => ({
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

export const EditTriggerPage: FC = () => {
  const { triggerId } = useTypedParams<{ triggerId: number }>();
  const willCreate = triggerId === undefined;

  const history = useHistory();
  const { enqueueSubmitResult } = useFormNotification("トリガー", willCreate);

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

  const { fields, insert, remove, swap } = useFieldArray({
    control,
    name: "conditions",
    keyName: "key", // NOTE: attr has 'id' field conflicts default key name
  });

  const trigger = useAsyncWithThrow(async () => {
    if (triggerId !== undefined) {
      return await aironeApiClient.getTrigger(triggerId);
    } else {
      return undefined;
    }
  }, []);

  const entity = useAsyncWithThrow(async () => {
    if (trigger.value) {
      return await aironeApiClient.getEntity(trigger.value.entity.id);
    } else {
      return undefined;
    }
  }, [trigger.value]);

  const handleSubmitOnValid = useCallback(
    async (trigger: Schema) => {
      const triggerCreateUpdate: TriggerParentUpdate = {
        ...trigger,
        entityId: trigger.entityId,
        conditions: trigger.conditions.map((condition) => {
          return {
            ...condition,
            attr: condition.attrId,
          };
        }),
        actions: trigger.actions.map((action) => {
          return {
            ...action,
            attr: action.attrId,
          };
        }),
      };
      if (triggerId !== undefined) {
        await aironeApiClient.updateTrigger(triggerId, triggerCreateUpdate);
        enqueueSubmitResult(true);
      } else {
        await aironeApiClient.createTrigger(triggerCreateUpdate);
        enqueueSubmitResult(true);
      }
    },
    [triggerId]
  );

  const handleCancel = async () => {
    history.goBack();
  };

  return (
    <Box>
      {entity.value ? (
        <EntityBreadcrumbs entity={entity.value} title="編集" />
      ) : (
        <EntityBreadcrumbs title="作成" />
      )}

      <PageHeader
        title={entity.value ? entity.value.name : "新規トリガーの作成"}
        description={entity.value && "トリガー編集"}
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
            <>
              {fields.map((field, index) => {
                return (
                  <Box key={field.key}>
                    <Controller
                      name={`conditions.${index}.attrId`}
                      control={control}
                      defaultValue={0}
                      render={({ field }) => (
                        <Select {...field} size="small" fullWidth>
                          <MenuItem></MenuItem>
                        </Select>
                      )}
                    />
                  </Box>
                );
              })}
            </>
          </StyledTableBody>
        </Table>

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
        </Table>
      </Container>
      {/*
      <Prompt
        when={isDirty && !isSubmitSuccessful}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
      */}
    </Box>
  );
};
