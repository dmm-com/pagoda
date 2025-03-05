import {
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, Autocomplete, Checkbox, TextField, Button } from "@mui/material";
import React, { Dispatch, FC, useState, SetStateAction } from "react";
import { useNavigate } from "react-router";

import { formatAdvancedSearchParams } from "../../services/entry/AdvancedSearch";
import { AironeModal } from "../common/AironeModal";

interface Props {
  openModal: boolean;
  setOpenModal: Dispatch<SetStateAction<boolean>>;
  attrNames: string[];
  initialAttrNames: string[];
  attrInfos: AdvancedSearchResultAttrInfo[];
}

export const AdvancedSearchModal: FC<Props> = ({
  openModal,
  setOpenModal,
  attrNames,
  initialAttrNames,
  attrInfos,
}) => {
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);

  const [selectedAttrNames, setSelectedAttrNames] = useState(initialAttrNames);
  const [hasReferral, setHasReferral] = useState(
    params.get("has_referral") === "true",
  );

  const handleUpdatePageURL = () => {
    const params = formatAdvancedSearchParams({
      attrsFilter: Object.fromEntries(
        selectedAttrNames.map((attrName) => {
          const attrInfo = attrInfos.find((info) => info.name === attrName);
          return [
            attrName,
            {
              filterKey:
                attrInfo?.filterKey ??
                AdvancedSearchResultAttrInfoFilterKeyEnum.CLEARED,
              keyword: attrInfo?.keyword ?? "",
            },
          ];
        }),
      ),
      hasReferral,
      baseParams: new URLSearchParams(location.search),
    });

    // Update Page URL parameters
    navigate({
      pathname: location.pathname,
      search: "?" + params.toString(),
    });
    navigate(0);
  };

  return (
    <AironeModal
      title={"検索属性の再設定"}
      open={openModal}
      onClose={() => setOpenModal(false)}
    >
      <Autocomplete
        options={attrNames}
        defaultValue={initialAttrNames}
        onChange={(_, value: Array<string>) => setSelectedAttrNames(value)}
        renderInput={(params) => (
          <TextField {...params} variant="outlined" placeholder="属性を選択" />
        )}
        multiple
        sx={{ width: "100%", margin: "20px 0" }}
      />
      <Box display="flex" justifyContent="center">
        <Box>
          参照アイテムも含める
          <Checkbox
            checked={hasReferral}
            onChange={(e) => setHasReferral(e.target.checked)}
          />
        </Box>
      </Box>
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
          onClick={() => setOpenModal(false)}
        >
          キャンセル
        </Button>
      </Box>
    </AironeModal>
  );
};
