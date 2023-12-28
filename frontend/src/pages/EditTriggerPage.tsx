import { Box } from "@mui/material";
import React, { FC } from "react";

import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

export const EditTriggerPage: FC = () => {
  const { triggerId } = useTypedParams<{ triggerId: number }>();

  const willCreate = triggerId === undefined;

  const trigger = useAsyncWithThrow(async () => {
    if (triggerId !== undefined) {
      return await aironeApiClientV2.getTrigger(triggerId);
    } else {
      return undefined;
    }
  }, []);

  const entity = useAsyncWithThrow(async () => {
    if (trigger.value) {
      return await aironeApiClientV2.getEntity(trigger.value.entity.id);
    } else {
      return undefined;
    }
  }, [trigger.value]);

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
        {/*
        <SubmitButton
          name="保存"
          disabled={!isDirty || !isValid || isSubmitting || isSubmitSuccessful}
          isSubmitting={isSubmitting}
          handleSubmit={handleSubmit(handleSubmitOnValid)}
          handleCancel={handleCancel}
        />
        */}
      </PageHeader>

      {/*
      <Prompt
        when={isDirty && !isSubmitSuccessful}
        message="編集した内容は失われてしまいますが、このページを離れてもよろしいですか？"
      />
      */}
    </Box>
  );
};
