import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getEntity } from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { useAsync } from "react-use";
import EntityForm from "../components/entity/EntityForm";
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

  const handleTabChanage = (event, newValue) => {
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

      <Tabs value={tabValue}>
        <Tab label="編集" index={0} />
        <Tab label="設定" index={1} />
      </Tabs>

      <div hidden={tabValue !== 0}>hoge</div>

      <div hidden={tabValue !== 1}>fuga</div>

      {!entity.loading && (
        <EntityForm
          initName={entity.value.name}
          initNote={entity.value.note}
          initIsTopLevel={entity.value.isTopLevel}
          initAttributes={entity.value.attributes}
        />
      )}
    </div>
  );
}
