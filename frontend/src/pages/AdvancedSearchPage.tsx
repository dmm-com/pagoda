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
import React, { FC, SyntheticEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { AutocompleteWithAllSelector } from "../components/common/AutocompleteWithAllSelector";
import { PageHeader } from "../components/common/PageHeader";
import { useAsyncWithThrow } from "../hooks/useAsyncWithThrow";
import { aironeApiClient } from "../repository/AironeApiClient";
import { formatAdvancedSearchParams } from "../services/entry/AdvancedSearch";

import { advancedSearchResultPath, topPath } from "Routes";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";

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
  const [selectedEntities, setSelectedEntities] = useState<Array<EntityList>>(
    []
  );
  const [selectedAttrs, setSelectedAttrs] = useState<Array<string>>([]);
  const [searchAllEntities, setSearchAllEntities] = useState(false);
  const [hasReferral, setHasReferral] = useState(false);
  const [entityName, setEntityName] = useState("");
  const [attrName, setAttrName] = useState("");

  const entities = useAsyncWithThrow(async () => {
    const entities = await aironeApiClient.getEntities();
    return entities.results;
  });

  const attrs = useAsyncWithThrow(async () => {
    if (selectedEntities.length > 0 || searchAllEntities) {
      return await aironeApiClient.getEntityAttrs(
        selectedEntities.map((e) => e.id),
        searchAllEntities
      );
    }
    return [];
  }, [selectedEntities, searchAllEntities]);

  const searchParams = useMemo(() => {
    return formatAdvancedSearchParams({
      attrsFilter: Object.fromEntries(
        selectedAttrs.map((attr) => [
          attr,
          {
            filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
            keyword: "",
          },
        ])
      ),
      entityIds: selectedEntities.map((e) => e.id.toString()),
      searchAllEntities,
      hasReferral,
    });
  }, [selectedEntities, searchAllEntities, selectedAttrs, hasReferral]);

  const handleChangeInputEntityName = (
    event: SyntheticEvent,
    value: string,
    reason: AutocompleteInputChangeReason
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
    reason: AutocompleteInputChangeReason
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
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">高度な検索</Typography>
      </AironeBreadcrumbs>

      <PageHeader title="高度な検索">
        <StyledFlexBox>
          <Button
            variant="contained"
            color="secondary"
            component={Link}
            to={`${advancedSearchResultPath()}?${searchParams}`}
            disabled={selectedEntities.length === 0 && !searchAllEntities}
          >
            検索
          </Button>
        </StyledFlexBox>
      </PageHeader>

      <Container>
        <StyledFlexColumnBox>
          <StyledTypography variant="h4">検索対象のモデル</StyledTypography>

          <Autocomplete
            options={entities.value ?? []}
            getOptionLabel={(option: EntityList) => option.name}
            value={selectedEntities}
            inputValue={entityName}
            disabled={entities.loading}
            onChange={(_, value: Array<EntityList>) =>
              setSelectedEntities(value)
            }
            onInputChange={handleChangeInputEntityName}
            renderInput={(params) => (
              <TextField
                {...params}
                variant="outlined"
                placeholder="モデルを選択"
              />
            )}
            multiple
            disableCloseOnSelect
            fullWidth
          />
          <Box>
            検索対象を絞り込まない
            <Checkbox
              checked={searchAllEntities}
              onChange={(e) => setSearchAllEntities(e.target.checked)}
            />
          </Box>
        </StyledFlexColumnBox>

        <StyledFlexColumnBox>
          <StyledTypography variant="h4">属性</StyledTypography>

          {!attrs.loading && (
            <AutocompleteWithAllSelector
              selectAllLabel="すべて選択"
              options={attrs.value ?? []}
              value={selectedAttrs}
              inputValue={attrName}
              onChange={(_, value: Array<string>) => setSelectedAttrs(value)}
              onInputChange={handleChangeInputAttrName}
              renderInput={(params) => (
                <TextField
                  {...params}
                  variant="outlined"
                  placeholder="属性を選択"
                />
              )}
              multiple
              disableCloseOnSelect
              fullWidth
            />
          )}
          <Box>
            参照アイテムも含める
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
