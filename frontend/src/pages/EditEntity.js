import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getEntity } from "../utils/AironeAPIClient";
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
      return getEntity(entityId);
    }
    return Promise.resolve({});
  });

  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  }

  return (
    <div>
      <AironeBreadcrumbs>
        <Typography component={Link} to="/new-ui/">
          Top
        </Typography>
        <Typography component={Link} to={`/new-ui/entities`}>
          エンティティ一覧
        </Typography>
        <Typography color="textPrimary">エンティティ編集</Typography>
      </AironeBreadcrumbs>

      <Tabs value={tabValue} onChange={handleTabChange}>
        <Tab label="編集" index={0} />
        <Tab label="設定" index={1} />
      </Tabs>

      <div hidden={tabValue !== 0}>
      {!entity.loading && (
        <EntityForm
          initName={entity.value.name}
          initNote={entity.value.note}
          initIsTopLevel={entity.value.isTopLevel}
          initAttributes={entity.value.attributes}
        />
      )}
      </div>
      <div hidden={tabValue !== 1}>
        <WebhookForm
          entityId={entityId}
        />
      </div>

    </div>
  );
}
