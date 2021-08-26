import React from "react";
import { Link, useParams } from "react-router-dom";
import { getEntity } from "../utils/AironeAPIClient";
import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import Typography from "@material-ui/core/Typography";
import { useAsync } from "react-use";
import EntityForm from "../components/entity/EntityForm";

export default function EditEntity({}) {
  const { entityId } = useParams();

  const entity = useAsync(async () => {
    if (entityId !== undefined) {
      return getEntity(entityId);
    }
    return Promise.resolve({});
  });

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
