import LockIcon from "@mui/icons-material/Lock";
import { Box, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import { topPath, entitiesPath, entityEntriesPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";

const StyledBox = styled(Box)({
  display: "flex",
});

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
        エンティティ一覧
      </Typography>
      {entity && (
        <StyledBox>
          <Typography component={Link} to={entityEntriesPath(entity.id)}>
            {entity.name}
          </Typography>
          {!entity.isPublic && <LockIcon />}
        </StyledBox>
      )}
      {attr && <Typography color="textPrimary">{attr}</Typography>}
      {title && <Typography color="textPrimary">{title}</Typography>}
    </AironeBreadcrumbs>
  );
};
