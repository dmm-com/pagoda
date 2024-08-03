import AppsIcon from "@mui/icons-material/Apps";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { Box, Chip, Grid, IconButton, Stack, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useEffect, useState } from "react";
import { useHistory } from "react-router-dom";

import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { useTypedParams } from "../hooks/useTypedParams";

import { entryDetailsPath, restoreEntryPath } from "Routes";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntryAttributes } from "components/entry/EntryAttributes";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryReferral } from "components/entry/EntryReferral";
import { aironeApiClient } from "repository/AironeApiClient";

const FlexBox = styled(Box)(({}) => ({
  display: "flex",
  flexDirection: "column",
  flexGrow: "1",
}));

const ChipBox = styled(Box)({
  display: "flex",
  alignItems: "center",
  gap: "20px",
});

const MenuBox = styled(Box)(({}) => ({
  width: "50px",
}));

const ContentBox = styled(Box)(({}) => ({
  padding: "0 16px 64px",
}));

const LeftGrid = styled(Grid)(({}) => ({
  borderRight: "1px solid",
  borderColor: "rgba(0, 0, 0, 0.12)",
}));

const RightGrid = styled(Grid)(({}) => ({
  borderLeft: "1px solid",
  borderColor: "rgba(0, 0, 0, 0.12)",
}));

const StyledTypography = styled(Typography)(({}) => ({
  /* an anchor link adjusted fixed headers etc. */
  scrollMarginTop: "180px",
  marginBottom: "16px",
  fontSize: "32px",
  textAlign: "center",
}));

interface Props {
  excludeAttrs?: string[];
  additionalContents?: {
    name: string;
    label: string;
    content: JSX.Element;
  }[];
  sideContent?: JSX.Element;
}

export const EntryDetailsPage: FC<Props> = ({
  excludeAttrs = [],
  additionalContents = [],
  sideContent = <Box />,
}) => {
  const { entityId, entryId } = useTypedParams<{
    entityId: number;
    entryId: number;
  }>();
  const history = useHistory();

  const [entryAnchorEl, setEntryAnchorEl] = useState<HTMLButtonElement | null>(
    null
  );

  const entry = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntry(entryId);
  }, [entryId]);

  useEffect(() => {
    // When user specifies invalid entityId, redirect to the page that is correct entityId
    if (!entry.loading && entry.value?.schema?.id != entityId) {
      history.replace(entryDetailsPath(entry.value?.schema?.id ?? 0, entryId));
    }

    // If it'd been deleted, show restore-entry page instead
    if (!entry.loading && entry.value?.isActive === false) {
      history.replace(
        restoreEntryPath(entry.value?.schema?.id ?? "", entry.value?.name ?? "")
      );
    }
  }, [entry.loading]);

  return (
    <FlexBox>
      <EntryBreadcrumbs entry={entry.value} />

      <PageHeader title={entry.value?.name ?? ""} description="アイテム詳細">
        <ChipBox>
          <Stack direction="row" spacing={1}>
            {[
              {
                name: "attr_list",
                label: "項目一覧",
              },
              ...additionalContents,
            ].map((content) => {
              return (
                <Chip
                  key={content.name}
                  id={"chip_" + content.name}
                  component="a"
                  href={`#${content.name}`}
                  icon={<ArrowDropDownIcon />}
                  label={content.label}
                  clickable={true}
                  variant="outlined"
                />
              );
            })}
          </Stack>
          <MenuBox>
            <IconButton
              id="entryMenu"
              onClick={(e) => {
                setEntryAnchorEl(e.currentTarget);
              }}
            >
              <AppsIcon />
            </IconButton>
            <EntryControlMenu
              entityId={entityId}
              entryId={entryId}
              anchorElem={entryAnchorEl}
              handleClose={() => setEntryAnchorEl(null)}
            />
          </MenuBox>
        </ChipBox>
      </PageHeader>

      <Grid container flexGrow="1" columns={6}>
        <LeftGrid item xs={1}>
          <EntryReferral entryId={entryId} />
        </LeftGrid>
        <Grid item xs={4}>
          {[
            {
              name: "attr_list",
              label: "項目一覧",
              content: entry.loading ? (
                <Loading />
              ) : (
                <EntryAttributes
                  attributes={
                    entry.value?.attrs.filter(
                      (attr) => !excludeAttrs.includes(attr.schema.name)
                    ) ?? []
                  }
                />
              ),
            },
            ...additionalContents,
          ].map((content) => {
            return (
              <ContentBox key={content.name}>
                <StyledTypography id={content.name}>
                  {content.label}
                </StyledTypography>
                {content.content}
              </ContentBox>
            );
          })}
        </Grid>
        <RightGrid item xs={1}>
          {sideContent}
        </RightGrid>
      </Grid>
    </FlexBox>
  );
};
