import {
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  EntityList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Autocomplete,
  AutocompleteInputChangeReason,
  Box,
  Button,
  Checkbox,
  Container,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, SyntheticEvent, useMemo, useState } from "react";
import { Link } from "react-router";

import { AutocompleteWithAllSelector } from "../components/common/AutocompleteWithAllSelector";
import { PageHeader } from "../components/common/PageHeader";
import { usePagodaSWR } from "../hooks/usePagodaSWR";
import { aironeApiClient } from "../repository/AironeApiClient";
import { formatAdvancedSearchParams } from "../services/entry/AdvancedSearch";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { useTranslation } from "hooks/useTranslation";
import { advancedSearchResultPath, topPath } from "routes/Routes";

const StyledFlexBox = styled(Box)({
  display: "flex",
  justifyContent: "center",
});

const StyledFlexColumnBox = styled(Box)({
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  marginBottom: "48px",
});

const StyledTypography = styled(Typography)({
  marginBottom: "16px",
});

export const AdvancedSearchPage: FC = () => {
  const { t } = useTranslation();
  const [selectedEntities, setSelectedEntities] = useState<Array<EntityList>>(
    [],
  );
  const [selectedAttrs, setSelectedAttrs] = useState<Array<string>>([]);
  const [searchAllEntities, setSearchAllEntities] = useState(false);
  const [hasReferral, setHasReferral] = useState(false);
  const [entityName, setEntityName] = useState("");
  const [attrName, setAttrName] = useState("");

  const { data: entities, isLoading: entitiesLoading } = usePagodaSWR(
    ["entities"],
    async () => {
      const entities = await aironeApiClient.getEntities();
      return entities.results;
    },
  );

  const entityIds = selectedEntities.map((e) => e.id);
  const { data: attrs, isLoading: attrsLoading } = usePagodaSWR(
    selectedEntities.length > 0 || searchAllEntities
      ? ["entityAttrs", entityIds, searchAllEntities]
      : null,
    () => aironeApiClient.getEntityAttrs(entityIds, searchAllEntities),
  );

  const searchParams = useMemo(() => {
    return formatAdvancedSearchParams({
      attrsFilter: Object.fromEntries(
        selectedAttrs.map((attr) => [
          attr,
          {
            filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
            keyword: "",
          },
        ]),
      ),
      entityIds: selectedEntities.map((e) => e.id.toString()),
      searchAllEntities,
      hasReferral,
    });
  }, [selectedEntities, searchAllEntities, selectedAttrs, hasReferral]);

  const handleChangeInputEntityName = (
    event: SyntheticEvent,
    value: string,
    reason: AutocompleteInputChangeReason,
  ) => {
    // Not to clear input value on selecting an item
    if (reason === "reset") {
      return;
    }
    setEntityName(value);
  };

  const handleChangeInputAttrName = (
    event: SyntheticEvent,
    value: string,
    reason: AutocompleteInputChangeReason,
  ) => {
    // Not to clear input value on selecting an item
    if (reason === "reset") {
      return;
    }
    setAttrName(value);
  };

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">
          {t("advancedSearch.page.breadcrumb")}
        </Typography>
      </AironeBreadcrumbs>

      <PageHeader title={t("advancedSearch.page.title")}>
        <StyledFlexBox>
          <Button
            variant="contained"
            color="secondary"
            component={Link}
            to={`${advancedSearchResultPath()}?${searchParams}`}
            disabled={selectedEntities.length === 0 && !searchAllEntities}
          >
            {t("advancedSearch.page.search")}
          </Button>
        </StyledFlexBox>
      </PageHeader>

      <Container>
        <StyledFlexColumnBox>
          <StyledTypography variant="h4">
            {t("advancedSearch.page.targetModel")}
          </StyledTypography>

          <Autocomplete
            options={entities ?? []}
            getOptionLabel={(option: EntityList) => option.name}
            value={selectedEntities}
            inputValue={entityName}
            disabled={entitiesLoading}
            onChange={(_, value: Array<EntityList>) =>
              setSelectedEntities(value)
            }
            onInputChange={handleChangeInputEntityName}
            renderInput={(params) => (
              <TextField
                {...params}
                variant="outlined"
                placeholder={t("advancedSearch.page.selectModelPlaceholder")}
              />
            )}
            multiple
            disableCloseOnSelect
            fullWidth
          />
          <Box>
            {t("advancedSearch.page.searchAllEntities")}
            <Checkbox
              checked={searchAllEntities}
              onChange={(e) => setSearchAllEntities(e.target.checked)}
            />
          </Box>
        </StyledFlexColumnBox>

        <StyledFlexColumnBox>
          <StyledTypography variant="h4">
            {t("advancedSearch.page.attr")}
          </StyledTypography>

          <AutocompleteWithAllSelector
            selectAllLabel={t("advancedSearch.page.selectAll")}
            options={Array.from(new Set(attrs?.map((x) => x.name) ?? []))}
            value={selectedAttrs}
            inputValue={attrName}
            disabled={attrsLoading}
            onChange={(_, value: Array<string>) => setSelectedAttrs(value)}
            onInputChange={handleChangeInputAttrName}
            renderInput={(params) => (
              <TextField
                {...params}
                variant="outlined"
                placeholder={t("advancedSearch.page.selectAttrPlaceholder")}
              />
            )}
            multiple
            disableCloseOnSelect
            fullWidth
          />
          <Box>
            {t("advancedSearch.page.includeReferral")}
            <Checkbox
              checked={hasReferral}
              onChange={(e) => setHasReferral(e.target.checked)}
            />
          </Box>
        </StyledFlexColumnBox>
      </Container>
    </Box>
  );
};
