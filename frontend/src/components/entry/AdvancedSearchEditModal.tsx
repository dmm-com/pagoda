import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Button } from "@mui/material";
import { FC, useMemo } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";

import { AironeModal } from "components/common/AironeModal";
import { AttributeValueField } from "components/entry/entryForm/AttributeValueField";
import { Schema, schema } from "components/entry/entryForm/EntryFormSchema";
import { AttrsFilter } from "services/entry/AdvancedSearch";
import { getEntryAttributeValue } from "utils/common";
import { useSnackbar } from "notistack";
import { extractAdvancedSearchParams } from "services/entry/AdvancedSearch";

interface Props {
  openModal: boolean;
  handleClose: () => void;
  attrsFilter: AttrsFilter;
  targetAttrID: number;
  targetAttrtype: number;
  targetAttrname: string;
}

export const AdvancedSearchEditModal: FC<Props> = ({
  openModal,
  handleClose,
  attrsFilter,
  targetAttrID,
  targetAttrname,
  targetAttrtype,
}) => {
  const navigate = useNavigate();
  const attrValue = getEntryAttributeValue(targetAttrtype);
  const { enqueueSnackbar } = useSnackbar();
  const query = new URLSearchParams(location.search);
  console.log("[onix/AdvancedSearchEditModal] URLParams.entity:", query.get("entity"));

  const {
    hasReferral,
    referralName,
    hintEntry,
  } = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return extractAdvancedSearchParams(params);
  }, [location.search]);

  const {
    formState: { isValid, isDirty, isSubmitting, isSubmitSuccessful },
    handleSubmit,
    reset,
    setError,
    setValue,
    control,
    trigger,
    getValues,
  } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onBlur",
  });

  const handleUpdateAttributeValue = () => {
    // create parameters to send API for bulk update
    const settingValue = getValues().attrs?.[targetAttrID]?.value
    const sendingAttrsFilter = Object.keys(attrsFilter).map((key) => {
      return {
        name: key,
        ...attrsFilter[key as keyof AttrsFilter],
      }
    });
    console.log("[onix/AdvancedSearchEditModal.handleSubmit(10)] hintEntry:", hintEntry);
    console.log("[onix/AdvancedSearchEditModal.handleSubmit(10)] referralName:", referralName);
    console.log("[onix/AdvancedSearchEditModal.handleSubmit(10)] targetAttrID:", targetAttrID);
    console.log("[onix/AdvancedSearchEditModal.handleSubmit(10)] sendingAttrsFilter:", sendingAttrsFilter);
    console.log("[onix/AdvancedSearchEditModal.handleSubmit(10)] settingValue:", settingValue);

    // TODO: call API to update attribute value in bulk
    enqueueSnackbar(`属性「${targetAttrname}」の一括更新のジョブを実行しました（順次結果が反映されます）。`, {
      variant: "success",
    });

    // Reset input context
    reset();

    // Close this modal
    handleClose();
  }

  return (
    <AironeModal
      title={"一括更新する（変更後の）値に更新"}
      open={openModal}
      onClose={handleClose}
    >
      <Box sx={{ width: "100%", margin: "20px 0" }}>
        <AttributeValueField
          control={control}
          setValue={setValue}
          type={targetAttrtype}
          schemaId={targetAttrID}
        />
      </Box>
      <Box display="flex" justifyContent="flex-end" my="8px">
        <Button
          variant="contained" color="secondary" sx={{ mx: "4px" }}
          onClick={handleUpdateAttributeValue}
        >
          更新
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
