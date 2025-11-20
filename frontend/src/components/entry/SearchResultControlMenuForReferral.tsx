import {
  AdvancedSearchResultAttrInfoFilterKeyEnum,
  EntityList,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import Check from "@mui/icons-material/Check";
import {
  Autocomplete,
  Box,
  Button,
  Divider,
  ListItemIcon,
  Menu,
  MenuItem,
  TextField,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { ChangeEvent, Dispatch, FC, KeyboardEvent, useState } from "react";
import { useAsync } from "react-use";

import { handleSelectFilterConditionsParams } from "./SearchResultsTableHead";

import { aironeApiClient } from "repository";

const StyledTextField = styled(TextField)({
  margin: "8px",
});

const StyledBox = styled(Box)({
  margin: "8px",
});

interface Props {
  referralFilter: string;
  referralIncludeModelIds: number[];
  referralExcludeModelIds: number[];
  anchorElem: HTMLButtonElement | null;
  handleClose: () => void;
  referralFilterDispatcher: Dispatch<
    ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  >;
  referralIncludeModelIdsDispatcher: Dispatch<number[]>;
  referralExcludeModelIdsDispatcher: Dispatch<number[]>;
  handleSelectFilterConditions: (
    params: handleSelectFilterConditionsParams,
  ) => void;
}

export const SearchResultControlMenuForReferral: FC<Props> = ({
  referralFilter,
  referralIncludeModelIds,
  referralExcludeModelIds,
  anchorElem,
  handleClose,
  referralFilterDispatcher,
  referralIncludeModelIdsDispatcher,
  referralExcludeModelIdsDispatcher,
  handleSelectFilterConditions,
}) => {
  const entities = useAsync(async () => {
    return await aironeApiClient.getEntities();
  });
  const handleKeyPressKeyword = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED);
      handleSelectFilterConditions({});
    }
  };

  const getDefaultFilterKey = (): AdvancedSearchResultAttrInfoFilterKeyEnum => {
    const params = new URLSearchParams(location.search);

    switch (params.get("referral_name")) {
      case undefined:
        return AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED;
      case "\\":
        return AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY;
      case "*":
        return AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY;
      default:
        return AdvancedSearchResultAttrInfoFilterKeyEnum.TEXT_CONTAINED;
    }
  };

  const [filterKey, setFilterKey] =
    useState<AdvancedSearchResultAttrInfoFilterKeyEnum>(getDefaultFilterKey());
  const handleFilter = (key: AdvancedSearchResultAttrInfoFilterKeyEnum) => {
    // If the same filter item is selected, the filter is cleared.
    if (filterKey === key) {
      setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED);
      handleSelectFilterConditions({
        overwriteReferral: "",
        overwriteReferralIncludeModelIds: [],
        overwriteReferralExcludeModelIds: [],
      });
      return;
    }

    switch (key) {
      case AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY:
        setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY);
        handleSelectFilterConditions({ overwriteReferral: "\\" });
        break;

      case AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY:
        setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY);
        handleSelectFilterConditions({ overwriteReferral: "*" });
        break;
    }
  };

  return (
    <Menu
      open={Boolean(anchorElem)}
      onClose={() => handleClose()}
      anchorEl={anchorElem}
    >
      <StyledBox>
        <Button
          variant="outlined"
          fullWidth
          onClick={() => {
            setFilterKey(AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED);
            handleSelectFilterConditions({
              overwriteReferral: "",
              overwriteReferralIncludeModelIds: [],
              overwriteReferralExcludeModelIds: [],
            });
          }}
        >
          <Typography>クリア</Typography>
        </Button>
      </StyledBox>
      <Divider />
      <MenuItem
        onClick={() =>
          handleFilter(AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY)
        }
      >
        {filterKey === AdvancedSearchResultAttrInfoFilterKeyEnum.EMPTY && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>空白</Typography>
      </MenuItem>
      <MenuItem
        onClick={() =>
          handleFilter(AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY)
        }
      >
        {filterKey === AdvancedSearchResultAttrInfoFilterKeyEnum.NON_EMPTY && (
          <ListItemIcon>
            <Check />
          </ListItemIcon>
        )}
        <Typography>空白ではない</Typography>
      </MenuItem>
      <StyledTextField
        size="small"
        placeholder="次を含むテキスト"
        value={referralFilter}
        onChange={referralFilterDispatcher}
        onKeyPress={handleKeyPressKeyword}
      />
      <Autocomplete
        options={entities.value?.results ?? []}
        getOptionLabel={(option: EntityList) => option.name}
        value={entities.value?.results.filter((entity) =>
          referralIncludeModelIds.includes(entity.id),
        )}
        isOptionEqualToValue={(option, value) => option.id === value.id}
        disabled={entities.loading}
        onChange={(_, value) => {
          referralIncludeModelIdsDispatcher(value.map((v) => v.id));
          handleSelectFilterConditions({
            overwriteReferralIncludeModelIds: value.map((v) => String(v.id)),
          });
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            variant="outlined"
            placeholder="次のモデルを含む"
            size="small"
          />
        )}
        multiple
        sx={{ m: "8px", maxWidth: "250px" }}
      />
      <Autocomplete
        options={entities.value?.results ?? []}
        getOptionLabel={(option: EntityList) => option.name}
        value={entities.value?.results.filter((entity) =>
          referralExcludeModelIds.includes(entity.id),
        )}
        isOptionEqualToValue={(option, value) => option.id === value.id}
        disabled={entities.loading}
        onChange={(_, value) => {
          referralExcludeModelIdsDispatcher(value.map((v) => v.id));
          handleSelectFilterConditions({
            overwriteReferralExcludeModelIds: value.map((v) => String(v.id)),
          });
        }}
        renderInput={(params) => (
          <TextField
            {...params}
            variant="outlined"
            placeholder="次のモデルを含む"
            size="small"
          />
        )}
        multiple
        sx={{ m: "8px", maxWidth: "250px" }}
      />
    </Menu>
  );
};
