import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import LockIcon from "@mui/icons-material/Lock";
import { Typography } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { FlexBox } from "components/common/FlexBox";
import {
  topPath,
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
} from "routes/Routes";

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
        モデル一覧
      </Typography>
      {entry && (
        <FlexBox>
          <Typography component={Link} to={entityEntriesPath(entry.schema.id)}>
            {entry.schema.name}
          </Typography>
          {!entry.schema.isPublic && <LockIcon />}
        </FlexBox>
      )}
      {entry && (
        <FlexBox>
          <Typography
            component={Link}
            to={entryDetailsPath(entry.schema.id, entry.id)}
          >
            {entry.name}
          </Typography>
          {!entry.isPublic && <LockIcon />}
        </FlexBox>
      )}
      {title && <Typography color="textPrimary">{title}</Typography>}
    </AironeBreadcrumbs>
  );
};
