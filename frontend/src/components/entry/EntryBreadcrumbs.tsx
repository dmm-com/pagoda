import { EntryRetrieve } from "@dmm-com/airone-apiclient-typescript-fetch";
import LockIcon from "@mui/icons-material/Lock";
import { Typography } from "@mui/material";
import React, { FC } from "react";

import { AironeLink } from "components/common";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { FlexBox } from "components/common/FlexBox";
import {
  entitiesPath,
  entityEntriesPath,
  entryDetailsPath,
  topPath,
} from "routes/Routes";

interface Props {
  entry?: EntryRetrieve;
  title?: string;
}

export const EntryBreadcrumbs: FC<Props> = ({ entry, title }) => {
  return (
    <AironeBreadcrumbs>
      <Typography component={AironeLink} to={topPath()}>
        Top
      </Typography>
      <Typography component={AironeLink} to={entitiesPath()}>
        モデル一覧
      </Typography>
      {entry && (
        <FlexBox>
          <Typography
            component={AironeLink}
            to={entityEntriesPath(entry.schema.id)}
          >
            {entry.schema.name}
          </Typography>
          {!entry.schema.isPublic && <LockIcon />}
        </FlexBox>
      )}
      {entry && (
        <FlexBox>
          <Typography
            component={AironeLink}
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
