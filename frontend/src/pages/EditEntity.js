import Typography from "@material-ui/core/Typography";
import React from "react";
import { Link, useParams } from "react-router-dom";
import { useAsync } from "react-use";

import AironeBreadcrumbs from "../components/common/AironeBreadcrumbs";
import EntityForm from "../components/entity/EntityForm";
import { getEntities, getEntity } from "../utils/AironeAPIClient";

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
  );
}
