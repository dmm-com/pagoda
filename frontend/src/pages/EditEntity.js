import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getEntities, getEntity } from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { useAsync } from "react-use";
import EntityForm from "../components/entity/EntityForm";
import WebhookForm from "../components/webhook/WebhookForm";
import Tab from "@material-ui/core/Tab";
import Tabs from "@material-ui/core/Tabs";

export default function EditEntity({}) {
  const { entityId } = useParams();

  const entity = useAsync(async () => {
    if (entityId !== undefined) {
      return getEntity(entityId).then((resp) => resp.json());
    }
    return Promise.resolve({});
  });

  const referralEntities = useAsync(async () => {
    if (entityId === undefined) {
      return getEntities()
        .then((resp) => resp.json())
        .then((data) => data.entities);
    }
    return Promise.resolve([]);
  });

  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to={`/new-ui/entities`}>
          エンティティ一覧
        </Typography>
        {/* TODO consider loading case */}
        {!entity.loading && (
          <Typography
            component={Link}
            to={`/new-ui/entities/${entityId}/entries`}
          >
            {entity.value.name}
          </Typography>
        )}
        <Typography color="textPrimary">エンティティ編集</Typography>
      </AironeBreadcrumbs>

      <Tabs value={tabValue} onChange={handleTabChange}>
        <Tab label="編集" index={0} />
        <Tab label="設定" index={1} />
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
        <WebhookForm entityId={entityId} />
      </div>
    </div>
  );
}
