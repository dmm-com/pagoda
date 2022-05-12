import { Box, Typography } from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "react-use";

import { aironeApiClientV2 } from "../apiclient/AironeApiClientV2";
import { Loading } from "../components/common/Loading";
import { getWebhooks } from "../utils/AironeAPIClient";
import { useTypedParams } from "../hooks/useTypedParams";

import { entitiesPath, entityEntriesPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { PageHeader } from "components/common/PageHeader";
import { EntityForm } from "components/entity/EntityForm";

export const EditEntityPage: FC = () => {
  const { entityId } = useTypedParams<{ entityId: number }>();

  const [entityInfo, setEntityInfo] = useState<{
    name: string;
    note: string;
    isTopLevel: boolean;
    attributes: { [key: string]: any }[];
  }>({
    name: "",
    note: "",
    isTopLevel: false,
    attributes: [],
  });

  const entity = useAsync(async () => {
    if (entityId !== undefined) {
      const resp = await aironeApiClientV2.getEntity(entityId);
      setEntityInfo({
        name: resp.name,
        note: resp.note,
        isTopLevel: resp.isToplevel,
        attributes:
          resp.attrs.map((attr) => {
            return { ...attr, refIds: attr.referrals.map((r) => r.id) };
          }) ?? [],
      });
      return resp;
    }
    return undefined;
  });

  const referralEntities = useAsync(async () => {
    const entities = await aironeApiClientV2.getEntities();
    return entities.results;
  });

  const webhooks = useAsync(async () => {
    if (entityId != null) {
      const resp = await getWebhooks(entityId);
      return await resp.json();
    } else {
      return [];
    }
  });
  const [submittable, setSubmittable] = useState<boolean>(false);

  if (entity.loading || referralEntities.loading || webhooks.loading) {
    return <Loading />;
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
        {entityId && (
          <Typography component={Link} to={entityEntriesPath(entityId)}>
            {entity?.value?.name ?? ""}
          </Typography>
        )}
        <Typography color="textPrimary">
          {entityId ? "エンティティ編集" : "新規エンティティの作成"}
        </Typography>
      </AironeBreadcrumbs>

      {/* TODO z-index, position: fixed, margin-top, background-color */}
      <PageHeader isSubmittable={submittable}>
        {entity?.value != null
          ? entity.value.name + "の編集"
          : "新規エンティティの作成"}
      </PageHeader>

      <Box sx={{ marginTop: "111px", paddingLeft: "10%", paddingRight: "10%" }}>
        {/*
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="編集" />
          <Tab label="設定" />
        </Tabs>

        <Box hidden={tabValue !== 0}>
          <EntityForm
            entity={entity.value}
            referralEntities={referralEntities.value}
          />
        </Box>
        <Box hidden={tabValue !== 1}>
          {entityId !== undefined ? (
            <WebhookForm entityId={entityId} webhooks={webhooks.value} />
          ) : (
            <Typography>
              未作成のエンティティはWebhookを設定できません。まずエンティティを作成してください。
            </Typography>
          )}
        </Box>
        */}

        <EntityForm
          entity={entity.value}
          entityInfo={entityInfo}
          setEntityInfo={setEntityInfo}
          referralEntities={referralEntities.value}
          setSubmittable={setSubmittable}
        />
      </Box>
    </Box>
  );
};
