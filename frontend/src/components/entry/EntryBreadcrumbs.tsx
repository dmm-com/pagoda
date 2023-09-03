import LockIcon from "@mui/icons-material/Lock";
import { Box, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  topPath,
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
} from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";

const StyledBox = styled(Box)({
  display: "flex",
});

interface Props {
  entry?: EntryRetrieve;
  title?: string;
}

export const EntryBreadcrumbs: FC<Props> = ({ entry, title }) => {
  return (
    <AironeBreadcrumbs>
      <Typography component={Link} to={topPath()}>
        Top
      </Typography>
      <Typography component={Link} to={entitiesPath()}>
        エンティティ一覧
      </Typography>
      {entry && (
        <StyledBox>
          <Typography component={Link} to={entityEntriesPath(entry.schema.id)}>
            {entry.schema.name}
          </Typography>
          {!entry.schema.isPublic && <LockIcon />}
        </StyledBox>
      )}
      {entry && (
        <StyledBox>
          <Typography
            component={Link}
            to={entryDetailsPath(entry.schema.id, entry.id)}
          >
            {entry.name}
          </Typography>
          {!entry.isPublic && <LockIcon />}
        </StyledBox>
      )}
      {title && <Typography color="textPrimary">{title}</Typography>}
    </AironeBreadcrumbs>
  );
};
