import {
  AdvancedSearchJoinAttrInfo,
  AdvancedSearchResultAttrInfo,
  AdvancedSearchResultAttrInfoFilterKeyEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { Box, Button, Checkbox, TextField } from "@mui/material";
import { Dispatch, FC, SetStateAction, useState } from "react";
import { useNavigate } from "react-router";

import { useTranslation } from "../../hooks/useTranslation";
import { formatAdvancedSearchParams } from "../../services/entry/AdvancedSearch";
import { AironeModal } from "../common/AironeModal";
import { AutocompleteWithAllSelector } from "../common/AutocompleteWithAllSelector";

interface Props {
  openModal: boolean;
  setOpenModal: Dispatch<SetStateAction<boolean>>;
  attrNames: string[];
  initialAttrNames: string[];
  attrInfos: AdvancedSearchResultAttrInfo[];
  joinAttrs: AdvancedSearchJoinAttrInfo[];
}

export const AdvancedSearchModal: FC<Props> = (props) => {
  const initialHasReferral =
    new URLSearchParams(location.search).get("has_referral") === "true";

  return props.openModal ? (
    <AdvancedSearchModalForm
      {...props}
      key={JSON.stringify([props.initialAttrNames, initialHasReferral])}
      initialHasReferral={initialHasReferral}
    />
  ) : null;
};

const AdvancedSearchModalForm: FC<Props & { initialHasReferral: boolean }> = ({
  openModal,
  setOpenModal,
  attrNames,
  initialAttrNames,
  attrInfos,
  joinAttrs,
  initialHasReferral,
}) => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedAttrNames, setSelectedAttrNames] = useState(initialAttrNames);
  const [hasReferral, setHasReferral] = useState(initialHasReferral);

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
      joinAttrs: joinAttrs.filter((joinAttr) =>
        selectedAttrNames.includes(joinAttr.name),
      ),
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
      title={t("advancedSearch.modal.resetAttrTitle")}
      open={openModal}
      onClose={() => setOpenModal(false)}
    >
      <AutocompleteWithAllSelector
        selectAllLabel={t("advancedSearch.page.selectAll")}
        options={attrNames}
        value={selectedAttrNames}
        onChange={(_, value: Array<string>) => setSelectedAttrNames(value)}
        renderInput={(params) => (
          <TextField
            {...params}
            variant="outlined"
            placeholder={t("advancedSearch.modal.selectAttrPlaceholder")}
          />
        )}
        multiple
        sx={{ width: "100%", margin: "20px 0" }}
      />
      <Box display="flex" justifyContent="center">
        <Box>
          {t("advancedSearch.modal.includeReferral")}
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
          {t("common.save")}
        </Button>
        <Button
          variant="outlined"
          color="primary"
          sx={{ mx: "4px" }}
          onClick={() => setOpenModal(false)}
        >
          {t("common.cancel")}
        </Button>
      </Box>
    </AironeModal>
  );
};
