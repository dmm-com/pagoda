import Tab from "@material-ui/core/Tab";
import Tabs from "@material-ui/core/Tabs";
import Typography from "@material-ui/core/Typography";
import React, { FC, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import { entitiesPath, entityEntriesPath, topPath } from "../Routes";
import { AironeBreadcrumbs } from "../components/common/AironeBreadcrumbs";
import { EntityForm } from "../components/entity/EntityForm";
import { WebhookForm } from "../components/webhook/WebhookForm";
import { getEntities, getEntity } from "../utils/AironeAPIClient";

export const EditEntity: FC = () => {
  const { entityId } = useParams();

  const entity = useAsync(async () => {
    if (entityId !== undefined) {
      const resp = await getEntity(entityId);
      return await resp.json();
    }
    return {};
  });

  const referralEntities = useAsync(async () => {
    if (entityId === undefined) {
      const resp = await getEntities();
      const data = await resp.json();
      return data.entities;
    }
    return [];
  });

  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography component={Link} to={entitiesPath()}>
          エンティティ一覧
        </Typography>
        {/* TODO consider loading case */}
        {!entity.loading && (
          <Typography component={Link} to={entityEntriesPath(entityId)}>
            {entity.value.name}
          </Typography>
        )}
        <Typography color="textPrimary">エンティティ編集</Typography>
      </AironeBreadcrumbs>

      <Tabs value={tabValue} onChange={handleTabChange}>
        <Tab label="編集" />
        <Tab label="設定" />
      </Tabs>

      <div hidden={tabValue !== 0}>
        {!entity.loading && !referralEntities.loading && (
          <EntityForm
            entity={{
              id: entityId,
              name: entity.value.name,
              note: entity.value.note,
              isTopLevel: entity.value.is_toplevel,
              attributes: entity.value.attributes,
            }}
            referralEntities={referralEntities.value}
          />
        )}
      </div>
      <div hidden={tabValue !== 1}>
        {entityId !== undefined ? (
          <WebhookForm entityId={entityId} />
        ) : (
          <Typography>
            未作成のエンティティはWebhookを設定できません。まずエンティティを作成してください。
          </Typography>
        )}
      </div>
    </div>
  );
};
