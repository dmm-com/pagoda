import { TriggerParentUpdate } from "@dmm-com/airone-apiclient-typescript-fetch";
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
import { useHistory } from "react-router-dom";

import { PageHeader } from "components/common/PageHeader";
import { SubmitButton } from "components/common/SubmitButton";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { Conditions } from "components/trigger/Conditions";
import { ActionForm } from "components/trigger/ActionForm";
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

  const entities = useAsyncWithThrow(async () => {
    const entities = await aironeApiClient.getEntities();
    return entities.results;
  });

  const trigger = useAsyncWithThrow(async () => {
    if (triggerId !== undefined) {
      return await aironeApiClient.getTrigger(triggerId);
    } else {
      return undefined;
    }
  }, []);

  const [entityId, setEntityId] = useState<number>();
  const entity = useAsyncWithThrow(async () => {
    if (entityId) {
      return await aironeApiClient.getEntity(entityId);
    } else {
      return undefined;
    }
  }, [entityId]);

  const handleSubmitOnValid = useCallback(
    async (trigger: Schema) => {
      const triggerCreateUpdate: TriggerParentUpdate = {
        id: triggerId,
        entityId: trigger.entity.id,
        conditions: [],
        actions: [],
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

  useEffect(() => {
    if (!trigger.loading && trigger.value != null) {
      // set defult value to React-hook-form
      reset(trigger.value);

      setEntityId(trigger.value.entity.id);
    }
  }, [trigger.loading]);

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
        <StyledFlexColumnBox>
          <Typography variant="h4">設定対象のエンティティ</Typography>

          <Controller
            name={`entity`}
            control={control}
            render={({ field }) => (
              <Autocomplete
                {...field}
                options={entities.value ?? []}
                getOptionLabel={(option: { id: number; name: string }) =>
                  option.name
                }
                isOptionEqualToValue={(option, value) => option.id === value.id}
                disabled={entities.loading}
                onChange={(_, value: { id: number; name: string } | null) => {
                  if (value) {
                    // set EntityId to state variable
                    setEntityId(value.id);

                    setValue(`entity`, value, {
                      shouldDirty: true,
                      shouldValidate: true,
                    });
                  }
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="outlined"
                    placeholder="エンティティを選択"
                  />
                )}
                disableCloseOnSelect
                fullWidth
              />
            )}
          />
        </StyledFlexColumnBox>

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
                <ActionForm control={control} entity={entity.value} />
              )}
            </StyledTableBody>
          </Table>
        </StyledFlexColumnBox>
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
