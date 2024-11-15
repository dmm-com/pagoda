import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { Autocomplete, Box, Button, TextField } from "@mui/material";
import React, { FC, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AironeModal } from "components/common/AironeModal";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { aironeApiClient } from "repository/AironeApiClient";
import { formatAdvancedSearchParams } from "services/entry/AdvancedSearch";

interface Props {
  targetEntityIds: number[];
  searchAllEntities: boolean;
  targetAttrname: string;
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  handleClose: () => void;
  refreshSearchResults: () => void;
}

export const AdvancedSearchJoinModal: FC<Props> = ({
  targetEntityIds,
  searchAllEntities,
  targetAttrname,
  joinAttrs,
  handleClose,
  refreshSearchResults,
}) => {
  const navigate = useNavigate();
  // This is join attributes that have been already been selected before.
  const currentAttrInfo: AdvancedSearchJoinAttrInfo | undefined =
    joinAttrs.find((attr) => attr.name === targetAttrname);

  const [selectedAttrNames, setSelectedAttrNames] = useState<Array<string>>(
    currentAttrInfo?.attrinfo.map((attr) => attr.name) ?? []
  );

  const referralAttrs = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntityAttrs(
      targetEntityIds,
      searchAllEntities,
      targetAttrname
    );
  }, [targetEntityIds, searchAllEntities, targetAttrname]);

  const handleUpdatePageURL = () => {
    // to prevent duplication of same name parameter
    const currentJoinAttrs = joinAttrs.filter(
      (attr) => attr.name !== targetAttrname
    );

    const newJoinAttrs = [
      ...currentJoinAttrs,
      {
        name: targetAttrname,
        attrinfo: selectedAttrNames.map((name) => {
          return {
            name: name,
            filterKey: AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
            keyword: "",
          };
        }),
      },
    ];
    const params = formatAdvancedSearchParams({
      baseParams: new URLSearchParams(location.search),
      joinAttrs: newJoinAttrs,
    });

    // update page by changing joined Attribute filter condition
    refreshSearchResults();

    // Update Page URL parameters
    navigate({
      pathname: location.pathname,
      search: "?" + params.toString(),
    });

    handleClose();
  };

  return (
    <AironeModal
      title={"結合するアイテムの属性名"}
      open={targetAttrname !== ""}
      onClose={handleClose}
    >
      <Autocomplete
        options={referralAttrs.value ?? []}
        value={selectedAttrNames}
        onChange={(_, value: Array<string>) => {
          setSelectedAttrNames(value);
        }}
        renderInput={(params) => (
          <TextField {...params} variant="outlined" placeholder="属性を選択" />
        )}
        multiple
        sx={{ width: "100%", margin: "20px 0" }}
      />
      <Box display="flex" justifyContent="flex-end" my="8px">
        <Button
          variant="contained"
          color="secondary"
          sx={{ mx: "4px" }}
          onClick={handleUpdatePageURL}
        >
          保存
        </Button>
        <Button
          variant="outlined"
          color="primary"
          sx={{ mx: "4px" }}
          onClick={handleClose}
        >
          キャンセル
        </Button>
      </Box>
    </AironeModal>
  );
};
