import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { Autocomplete, Box, Button, TextField } from "@mui/material";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { AironeModal } from "components/common/AironeModal";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { aironeApiClient } from "repository/AironeApiClient";
import { formatAdvancedSearchParams } from "services/entry/AdvancedSearch";

interface Props {
  targetAttrname: string;
  referralIds: number[] | undefined;
  joinAttrs: AdvancedSearchJoinAttrInfo[];
  setJoinAttrname: (name: string) => void;
}

export const AdvancedSearchJoinModal: FC<Props> = ({
  targetAttrname,
  referralIds,
  joinAttrs,
  setJoinAttrname,
}) => {
  const history = useHistory();
  // This is join attributes that have been already been selected before.
  const currentAttrInfo: AdvancedSearchJoinAttrInfo | undefined =
    joinAttrs.find((attr) => attr.name === targetAttrname);

  const [selectedAttrNames, setSelectedAttrNames] = useState<string[]>([]);

  const referralAttrs = useAsyncWithThrow(async () => {
    if (referralIds !== undefined && referralIds.length > 0) {
      return await aironeApiClient.getEntityAttrs(referralIds);
    }
    return [];
  }, [referralIds]);

  const closeModal = () => {
    setJoinAttrname("");
  };

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
        onChange={(_, value: string[]) => {
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
