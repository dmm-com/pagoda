import AppsIcon from "@mui/icons-material/Apps";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { Box, Chip, IconButton, Stack, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";
import { styled } from "@mui/material/styles";
import { FC, Suspense, useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntryAttributes } from "components/entry/EntryAttributes";
import { EntryBreadcrumbs } from "components/entry/EntryBreadcrumbs";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { EntryReferral } from "components/entry/EntryReferral";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { useTypedParams } from "hooks/useTypedParams";
import { aironeApiClient } from "repository/AironeApiClient";
import { entryDetailsPath, restoreEntryPath } from "routes/Routes";
import { TITLE_TEMPLATES } from "services";

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

const EntryDetailsContent: FC<Props> = ({
  excludeAttrs = [],
  additionalContents = [],
  sideContent = <Box />,
}) => {
  const { entityId, entryId } = useTypedParams<{
    entityId: number;
    entryId: number;
  }>();
  const navigate = useNavigate();

  const [entryAnchorEl, setEntryAnchorEl] = useState<HTMLButtonElement | null>(
    null,
  );

  const { data: entry } = usePagodaSWR(
    ["entry", entryId],
    () => aironeApiClient.getEntry(entryId),
    { suspense: true },
  );

  useEffect(() => {
    if (entry.schema?.id != entityId) {
      navigate(entryDetailsPath(entry.schema?.id ?? 0, entryId), {
        replace: true,
      });
    }

    if (entry.isActive === false) {
      navigate(restoreEntryPath(entry.schema?.id ?? "", entry.name ?? ""), {
        replace: true,
      });
    }
  }, [entry]);

  usePageTitle(TITLE_TEMPLATES.entryDetail, {
    prefix: entry.name,
  });

  return (
    <FlexBox>
      <EntryBreadcrumbs entry={entry} />

      <PageHeader title={entry.name ?? ""} description="アイテム詳細">
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
              permission={entry.permission}
              entityPermission={entry.schema?.permission}
            />
          </MenuBox>
        </ChipBox>
      </PageHeader>

      <Grid container flexGrow="1" columns={6}>
        <LeftGrid size={1}>
          <EntryReferral entryId={entryId} />
        </LeftGrid>
        <Grid size={4}>
          {[
            {
              name: "attr_list",
              label: "項目一覧",
              content: (
                <EntryAttributes
                  attributes={entry.attrs.filter(
                    (attr) => !excludeAttrs.includes(attr.schema.name),
                  )}
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
        <RightGrid size={1}>{sideContent}</RightGrid>
      </Grid>
    </FlexBox>
  );
};

export const EntryDetailsPage: FC<Props> = ({
  excludeAttrs = [],
  additionalContents = [],
  sideContent = <Box />,
}) => {
  return (
    <Suspense fallback={<Loading />}>
      <EntryDetailsContent
        excludeAttrs={excludeAttrs}
        additionalContents={additionalContents}
        sideContent={sideContent}
      />
    </Suspense>
  );
};
