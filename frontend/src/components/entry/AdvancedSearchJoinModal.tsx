import {
  AdvancedSearchResultAttrInfo,
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, Autocomplete, Checkbox, TextField, Button } from "@mui/material";
import React, { Dispatch, FC, useState, SetStateAction } from "react";
import { useHistory } from "react-router-dom";
import { aironeApiClient } from "../../repository/AironeApiClient";

import { formatAdvancedSearchParams } from "../../services/entry/AdvancedSearch";
import { AironeModal } from "../common/AironeModal";
import { useAsyncWithThrow } from "../..//hooks/useAsyncWithThrow";

interface Props {
  targetAttrname: string;
  referralIds: number[] | undefined;
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  setJoinAttrname: Dispatch<SetStateAction<string>>;
}

export const AdvancedSearchJoinModal: FC<Props> = ({
  targetAttrname,
  referralIds,
  joinAttrs,
  setJoinAttrname,
}) => {
  const history = useHistory();
  const params = new URLSearchParams(location.search);
  // This is join attributes that have been already been selected before.
  const currentAttrInfo: AdvancedSearchJoinAttrInfo | undefined = joinAttrs.find((attr) => attr.name === targetAttrname);

  const [selectedAttrNames, setSelectedAttrNames] = useState(Array());

  const referralAttrs = useAsyncWithThrow(async () => {
    if (referralIds !== undefined && referralIds.length > 0) {
      return await aironeApiClient.getEntityAttrs(referralIds);
    }
    return [];
  }, [referralIds]);

  const closeModal = () => {
    setJoinAttrname("");
  }

  const handleUpdatePageURL = () => {
    const joinAttrs = [{
      name: targetAttrname,
      attrinfo: selectedAttrNames.map((name) => {
        return {
          name: name,
        };
      }),
    }]

    const params = formatAdvancedSearchParams({
      joinAttrs: joinAttrs,
      baseParams: new URLSearchParams(location.search),
    });

    // Update Page URL parameters
    history.push({
      pathname: location.pathname,
      search: "?" + params.toString(),
    });
    history.go(0);
  };

  return (
    <AironeModal
      title={"結合するアイテムの属性名"}
      open={targetAttrname !== ""}
      onClose={() => closeModal()}
    >
      <Autocomplete
        options={referralAttrs.value?.map((x) => x.name) || []}
        defaultValue={currentAttrInfo?.attrinfo.map((x) => x.name) || []}
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
          onClick={() => closeModal()}
        >
          キャンセル
        </Button>
      </Box>
    </AironeModal>
  );
};
