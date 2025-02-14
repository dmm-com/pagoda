import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import LockIcon from "@mui/icons-material/Lock";
import { Typography } from "@mui/material";
import React, { FC } from "react";

import { AironeLink } from "components/common";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { FlexBox } from "components/common/FlexBox";
import { entitiesPath, entityEntriesPath, topPath } from "routes/Routes";

interface Props {
  entity?: EntityDetail;
  attr?: string;
  title?: string;
}

export const EntityBreadcrumbs: FC<Props> = ({ entity, attr, title }) => {
  return (
    <AironeBreadcrumbs>
      <Typography component={AironeLink} to={topPath()}>
        Top
      </Typography>
      <Typography component={AironeLink} to={entitiesPath()}>
        モデル一覧
      </Typography>
      {entity && (
        <FlexBox>
          <Typography component={AironeLink} to={entityEntriesPath(entity.id)}>
            {entity.name}
          </Typography>
          {!entity.isPublic && <LockIcon />}
        </FlexBox>
      )}
      {attr && <Typography color="textPrimary">{attr}</Typography>}
      {title && <Typography color="textPrimary">{title}</Typography>}
    </AironeBreadcrumbs>
  );
};
