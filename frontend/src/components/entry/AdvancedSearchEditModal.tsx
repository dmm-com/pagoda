import {
  AttributeData,
  EntryAttributeTypeTypeEnum,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import { zodResolver } from "@hookform/resolvers/zod";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  CircularProgress,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";

import { AironeModal } from "components/common/AironeModal";
import { AdvancedSearchTargetList } from "components/entry/AdvancedSearchTargetList";
import { AttributeValueField } from "components/entry/entryForm/AttributeValueField";
import { EditableEntryAttrs } from "components/entry/entryForm/EditableEntry";
import { Schema, schema } from "components/entry/entryForm/EntryFormSchema";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { EntryReferralList } from "services/Constants";
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
  selectedEntries?: Array<{ id: number; name: string; modelId: number }>;
  matchedCount?: number;
}

export const AdvancedSearchEditModal: FC<Props> = ({
  openModal,
  handleClose,
  modelIds,
  attrsFilter,
  targetAttrID,
  targetAttrname,
  targetAttrtype,
  selectedEntries = [],
  matchedCount = 0,
}) => {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation();
  const [references, setReferences] = useState<
    Record<
      number,
      Array<{ id: number; name: string; schema: { id: number; name: string } }>
    >
  >({});
  const [checking, setChecking] = useState(false);
  const [checkFailed, setCheckFailed] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [targetsExpanded, setTargetsExpanded] = useState(false);
  const [targetPage, setTargetPage] = useState(1);
  const [previewEntries, setPreviewEntries] = useState<
    Array<{ id: number; name: string; modelId: number }>
  >([]);
  const [previewCount, setPreviewCount] = useState(matchedCount);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewFailed, setPreviewFailed] = useState(false);
  const isAllMode = selectedEntries.length === 0;
  const targetPageSize = 10;
  const targetCount = isAllMode ? previewCount : selectedEntries.length;
  const targetPageCount = Math.ceil(targetCount / targetPageSize);
  const displayedTargetPage = Math.min(
    targetPage,
    Math.max(targetPageCount, 1),
  );
  const displayedTargets = isAllMode
    ? previewEntries
    : selectedEntries.slice(
        (displayedTargetPage - 1) * targetPageSize,
        displayedTargetPage * targetPageSize,
      );

  const closeModal = () => {
    setTargetsExpanded(false);
    setTargetPage(1);
    handleClose();
  };

  const { referralName, hintEntry } = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return extractAdvancedSearchParams(params);
  }, []);
  const sendingAttrsFilter = Object.keys(attrsFilter).map((key) => ({
    name: key,
    ...attrsFilter[key as keyof AttrsFilter],
  }));
  const previewQueryKey = JSON.stringify({
    modelIds,
    sendingAttrsFilter,
    referralName,
    hintEntry,
  });

  useEffect(() => {
    if (!openModal || !isAllMode || matchedCount === 0) return;
    let active = true;
    setPreviewLoading(true);
    setPreviewFailed(false);
    setPreviewCount(matchedCount);
    setPreviewEntries([]);
    aironeApiClient
      .advancedSearch(
        modelIds,
        sendingAttrsFilter,
        [],
        false,
        referralName,
        false,
        targetPage,
        targetPageSize,
        0,
        hintEntry,
      )
      .then((result) => {
        if (!active) return;
        setPreviewCount(result.totalCount);
        setPreviewEntries(
          result.values.map((value) => ({
            id: value.entry.id,
            name: value.entry.name,
            modelId: value.entity.id,
          })),
        );
      })
      .catch(() => {
        if (active) setPreviewFailed(true);
      })
      .finally(() => {
        if (active) setPreviewLoading(false);
      });
    return () => {
      active = false;
    };
  }, [openModal, isAllMode, targetPage, previewQueryKey]);

  useEffect(() => {
    const entriesToCheck = isAllMode ? previewEntries : selectedEntries;
    if (!openModal || entriesToCheck.length === 0) return;
    let active = true;
    setChecking(true);
    setCheckFailed(false);
    setReferences({});
    const loaded: typeof references = {};
    let nextIndex = 0;
    Promise.all(
      Array.from({ length: Math.min(8, entriesToCheck.length) }, async () => {
        while (nextIndex < entriesToCheck.length && active) {
          const entry = entriesToCheck[nextIndex++];
          if (!entry) break;
          const first = await aironeApiClient.getEntryReferral(entry.id, 1);
          const referrals = [...first.results];
          const pageCount = Math.ceil(
            first.count / EntryReferralList.MAX_ROW_COUNT,
          );
          for (let page = 2; page <= pageCount && active; page++) {
            const response = await aironeApiClient.getEntryReferral(
              entry.id,
              page,
            );
            referrals.push(...response.results);
          }
          loaded[entry.id] = referrals.filter((ref) => ref.id !== entry.id);
        }
      }),
    )
      .then(() => {
        if (active) setReferences(loaded);
      })
      .catch(() => {
        if (active) setCheckFailed(true);
      })
      .finally(() => {
        if (active) setChecking(false);
      });
    return () => {
      active = false;
    };
  }, [
    openModal,
    isAllMode,
    selectedEntries.map((entry) => entry.id).join(","),
    previewEntries.map((entry) => entry.id).join(","),
  ]);

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
    const perModelChoices: Array<Array<{ value?: string; label: string }>> =
      targetEntities.map(
        (e) => e.attrs.find((a) => a.name === targetAttrname)?.choices ?? [],
      );
    if (perModelChoices.some((c) => c.length === 0)) {
      // If any selected model lacks this attribute (or its choices list is
      // empty) there is no safe common choice to offer.
      return [];
    }
    const [first, ...rest] = perModelChoices;
    return (first ?? []).filter((choice) =>
      rest.every((other) => other.some((c) => c.value === choice.value)),
    );
  }, [isSelectLikeType, targetEntities, targetAttrname]);

  const handleUpdateAttributeValue = async () => {
    if (
      checking ||
      checkFailed ||
      updating ||
      previewLoading ||
      previewFailed ||
      targetCount === 0
    )
      return;
    setUpdating(true);
    // create parameters to send API for bulk update
    const settingValue = {
      [targetAttrID]: {
        index: 0,
        type: targetAttrtype,
        value: getValues().attrs?.[targetAttrID]?.value,
        schema: { id: targetAttrID },
      } as EditableEntryAttrs,
    };
    const bulkUpdateEntries = (modelId: number, value: AttributeData) => {
      return aironeApiClient.bulkUpdateEntries(
        modelId,
        value,
        sendingAttrsFilter,
        referralName,
        hintEntry,
        isAllMode
          ? undefined
          : selectedEntries
              .filter((entry) => entry.modelId === modelId)
              .map((entry) => entry.id),
      );
    };
    try {
      const updates = await Promise.all(
        (isAllMode
          ? modelIds
          : [...new Set(selectedEntries.map((entry) => entry.modelId))]
        ).map(async (modelId) => {
          const targetAttr = (
            await aironeApiClient.getEntityAttrs([modelId], false)
          ).find((attr) => attr.name === targetAttrname);
          if (!targetAttr)
            throw new Error("Attribute is missing from a selected model");
          const value = convertAttrsFormatCtoS({
            [targetAttr.id]: {
              ...settingValue[targetAttrID],
              schema: { id: targetAttr.id },
            } as EditableEntryAttrs,
          })[0]!;
          return { modelId, value };
        }),
      );
      await Promise.all(
        updates.map(({ modelId, value }) => bulkUpdateEntries(modelId, value)),
      );
      enqueueSnackbar(
        t("advancedSearch.editModal.bulkUpdateSucceeded", {
          attrName: targetAttrname,
        }),
        {
          variant: "success",
        },
      );

      // Reset input context
      reset();

      // Close this modal
      closeModal();
    } catch {
      enqueueSnackbar(t("advancedSearch.editModal.bulkUpdateFailed"), {
        variant: "error",
      });
    } finally {
      setUpdating(false);
    }
  };

  return (
    <AironeModal
      title={t("advancedSearch.editModal.bulkUpdateTitle")}
      open={openModal}
      onClose={closeModal}
    >
      {targetCount === 0 && !previewLoading ? (
        <Alert severity="info">{t("advancedSearch.editModal.noTargets")}</Alert>
      ) : (
        <Box>
          {isAllMode && (
            <Alert severity="warning" sx={{ mb: 1 }}>
              {t("advancedSearch.editModal.allMatchedNotice", {
                count: targetCount,
              })}
            </Alert>
          )}
          {(checking || previewLoading) && <CircularProgress size={20} />}
          {previewFailed && (
            <Alert severity="error">
              {t("advancedSearch.editModal.previewFailed")}
            </Alert>
          )}
          {checkFailed && (
            <Alert severity="error">
              {t("entry.control.referenceCheckFailure")}
            </Alert>
          )}
          <Accordion
            id="bulk-update-targets"
            expanded={targetsExpanded}
            onChange={(_, expanded) => setTargetsExpanded(expanded)}
            disableGutters
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>
                {t("advancedSearch.editModal.targets", {
                  count: targetCount,
                })}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {previewLoading && <CircularProgress size={20} />}
              <AdvancedSearchTargetList
                targets={displayedTargets.map((entry) => ({
                  ...entry,
                  referrals: references[entry.id],
                }))}
                totalCount={targetCount}
                page={displayedTargetPage}
                onPageChange={(nextPage) => {
                  setTargetPage(nextPage);
                  document
                    .getElementById("bulk-update-targets")
                    ?.scrollIntoView?.({ block: "start" });
                }}
                checkingReferences={checking || checkFailed || previewLoading}
              />
            </AccordionDetails>
          </Accordion>
        </Box>
      )}
      <Box
        role="group"
        aria-labelledby="bulk-update-attribute-label"
        sx={{ width: "100%", margin: "20px 0" }}
      >
        <Typography
          id="bulk-update-attribute-label"
          component="div"
          sx={{ mb: 1, fontWeight: 600 }}
        >
          {t("advancedSearch.editModal.valueLabel", {
            attrName: targetAttrname,
          })}
        </Typography>
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
          disabled={
            targetCount === 0 ||
            checking ||
            checkFailed ||
            updating ||
            previewLoading ||
            previewFailed
          }
        >
          {t("common.update")}
        </Button>
        <Button
          variant="outlined"
          color="primary"
          sx={{ mx: "4px" }}
          onClick={closeModal}
        >
          {t("common.cancel")}
        </Button>
      </Box>
    </AironeModal>
  );
};
