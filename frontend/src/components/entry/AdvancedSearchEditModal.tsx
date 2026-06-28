import {
  AttributeData,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import { Box, Button } from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, useMemo } from "react";
import { useForm } from "react-hook-form";

import { AironeModal } from "components/common/AironeModal";
import { AttributeValueField } from "components/entry/entryForm/AttributeValueField";
import { EditableEntryAttrs } from "components/entry/entryForm/EditableEntry";
import { Schema, schema } from "components/entry/entryForm/EntryFormSchema";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  AttrsFilter,
  extractAdvancedSearchParams,
} from "services/entry/AdvancedSearch";
import { convertAttrsFormatCtoS } from "services/entry/Edit";

interface Props {
  openModal: boolean;
  handleClose: () => void;
  modelIds: number[];
  attrsFilter: AttrsFilter;
  targetAttrID: number;
  targetAttrtype: number;
  targetAttrname: string;
}

export const AdvancedSearchEditModal: FC<Props> = ({
  openModal,
  handleClose,
  modelIds,
  attrsFilter,
  targetAttrID,
  targetAttrname,
  targetAttrtype,
}) => {
  const { enqueueSnackbar } = useSnackbar();

  const { referralName, hintEntry } = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return extractAdvancedSearchParams(params);
  }, []);

  const { reset, setValue, control, getValues } = useForm<Schema>({
    resolver: zodResolver(schema),
    mode: "onBlur",
  });

  const isSelectLikeType =
    targetAttrtype === EntryAttributeTypeTypeEnum.SELECT ||
    targetAttrtype === EntryAttributeTypeTypeEnum.MULTI_SELECT;

  // For SELECT / MULTI_SELECT bulk-edit the dropdown must offer only choices
  // valid for *every* selected model — picking a value missing from any model
  // would 400 that model's bulkUpdateEntries call. Fetch each selected model
  // in parallel and intersect its EntityAttr.choices (by value) so the picker
  // surfaces the safe common set.
  const swrKey =
    isSelectLikeType && openModal && modelIds.length > 0
      ? (["bulkEditSelectChoices", [...modelIds].sort().join(",")] as const)
      : null;
  const { data: targetEntities } = usePagodaSWR(swrKey, () =>
    Promise.all(modelIds.map((id) => aironeApiClient.getEntity(id))),
  );

  const targetChoices = useMemo(() => {
    if (!isSelectLikeType || !targetEntities || targetEntities.length === 0) {
      return undefined;
    }
    const perModelChoices = targetEntities.map(
      (e) => e.attrs.find((a) => a.name === targetAttrname)?.choices ?? [],
    );
    if (perModelChoices.some((c) => c.length === 0)) {
      // If any selected model lacks this attribute (or its choices list is
      // empty) there is no safe common choice to offer.
      return [];
    }
    const [first, ...rest] = perModelChoices;
    return first.filter((choice) =>
      rest.every((other) => other.some((c) => c.value === choice.value)),
    );
  }, [isSelectLikeType, targetEntities, targetAttrname]);

  const handleUpdateAttributeValue = () => {
    // create parameters to send API for bulk update
    const settingValue = {
      [targetAttrID]: {
        index: 0,
        type: targetAttrtype,
        value: getValues().attrs?.[targetAttrID]?.value,
        schema: { id: targetAttrID },
      } as EditableEntryAttrs,
    };
    const sendingAttrsFilter = Object.keys(attrsFilter).map((key) => {
      return {
        name: key,
        ...attrsFilter[key as keyof AttrsFilter],
      };
    });

    const bulkUpdateEntries = (modelId: number, value: AttributeData) => {
      return aironeApiClient
        .bulkUpdateEntries(
          modelId,
          value,
          sendingAttrsFilter,
          referralName,
          hintEntry,
        )
        .then(() => {
          enqueueSnackbar(
            `属性「${targetAttrname}」の一括更新のジョブを実行しました（順次結果が反映されます）。`,
            {
              variant: "success",
            },
          );

          // Reset input context
          reset();

          // Close this modal
          handleClose();
        });
    };
    // The aironeApiClient.bulkUpdateEntries would be called only one time in most cases.
    // because it's rare that multiple Models are specified for advanced search page.
    modelIds.forEach((modelId: number) => {
      // In case multiple Models are specified, fetch the attribute schema for each Model
      if (modelIds.length > 1) {
        aironeApiClient.getEntityAttrs([modelId], false).then((entityAttrs) => {
          const targetAttr = entityAttrs.find(
            (attr) => attr.name === targetAttrname,
          );
          if (targetAttr) {
            bulkUpdateEntries(
              modelId,
              convertAttrsFormatCtoS({
                [targetAttr.id]: {
                  ...settingValue[targetAttrID],
                  schema: { id: targetAttr.id },
                } as EditableEntryAttrs,
              })[0],
            );
          }
        });
      } else {
        bulkUpdateEntries(modelId, convertAttrsFormatCtoS(settingValue)[0]);
      }
    });
  };

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
          choices={targetChoices ?? undefined}
        />
      </Box>
      <Box display="flex" justifyContent="flex-end" my="8px">
        <Button
          variant="contained"
          color="secondary"
          sx={{ mx: "4px" }}
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
