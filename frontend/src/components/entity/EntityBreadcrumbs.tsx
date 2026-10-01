import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import LockIcon from "@mui/icons-material/Lock";
import { Tooltip, Typography } from "@mui/material";
import { FC } from "react";

import { AironeLink } from "components/common";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { FlexBox } from "components/common/FlexBox";
import { useTranslation } from "hooks/useTranslation";
import { entitiesPath, entityEntriesPath, topPath } from "routes/Routes";

interface Props {
  entity?: EntityDetail;
  attr?: string;
  title?: string;
}

export const EntityBreadcrumbs: FC<Props> = ({ entity, attr, title }) => {
  const { t } = useTranslation();

  return (
    <AironeBreadcrumbs>
      <Typography component={AironeLink} to={topPath()}>
        Top
      </Typography>
      <Typography component={AironeLink} to={entitiesPath()}>
        {t("entity.list.pageTitle")}
      </Typography>
      {entity && (
        <FlexBox>
          <Tooltip title={entity.name} placement="bottom-start">
            <Typography
              component={AironeLink}
              to={entityEntriesPath(entity.id)}
            >
              {entity.name}
            </Typography>
          </Tooltip>
          {!entity.isPublic && <LockIcon />}
        </FlexBox>
      )}
      {attr && (
        <Tooltip title={attr} placement="bottom-start">
          <Typography color="textPrimary">{attr}</Typography>
        </Tooltip>
      )}
      {title && (
        <Tooltip title={title} placement="bottom-start">
          <Typography color="textPrimary">{title}</Typography>
        </Tooltip>
      )}
    </AironeBreadcrumbs>
  );
};
