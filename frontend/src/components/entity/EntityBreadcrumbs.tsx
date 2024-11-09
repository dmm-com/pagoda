import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import LockIcon from "@mui/icons-material/Lock";
import { Typography } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { FlexBox } from "components/common/FlexBox";
import { topPath, entitiesPath, entityEntriesPath } from "routes/Routes";

interface Props {
  entity?: EntityDetail;
  attr?: string;
  title?: string;
}

export const EntityBreadcrumbs: FC<Props> = ({ entity, attr, title }) => {
  return (
    <AironeBreadcrumbs>
      <Typography component={Link} to={topPath()}>
        Top
      </Typography>
      <Typography component={Link} to={entitiesPath()}>
        モデル一覧
      </Typography>
      {entity && (
        <FlexBox>
          <Typography component={Link} to={entityEntriesPath(entity.id)}>
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
