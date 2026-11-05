import { FC, useCallback } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { ImportPreviewFailure } from "services/ImportPreviewJob";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const CommonImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const { t } = useTranslation();

  const handlePreview = useCallback(
    async (data: string | ArrayBuffer) => {
      const { jobIds, errors } =
        await aironeApiClient.startCommonImportPreview(data);
      if (jobIds.length === 0) {
        // Nothing can be previewed: every model in the file was rejected.
        throw new ImportPreviewFailure(
          errors.join(" / ") || t("notification.uploadFailed"),
        );
      }
      return jobIds;
    },
    [t],
  );

  const handleImport = useCallback(
    async (data: string | ArrayBuffer, previewJobIds: number[]) => {
      // An item file with several models has one preview per model, and the
      // import accepts a single preview id, so it is only passed when it is unambiguous.
      const { jobIds, error } = await aironeApiClient.importCommon(
        data,
        previewJobIds.length === 1 ? previewJobIds[0] : undefined,
      );
      if (jobIds.length === 0) {
        // Nothing was imported: every part of the file was rejected, so say why.
        throw new ImportPreviewFailure(
          error.join(" / ") || t("notification.uploadFailed"),
        );
      }
    },
    [t],
  );

  return (
    <AironeModal
      title={t("commonImport.title")}
      description={t("commonImport.description")}
      caption={t("commonImport.caption")}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <ImportForm
        handleImport={handleImport}
        handleCancel={closeImportModal}
        handlePreview={handlePreview}
      />
    </AironeModal>
  );
};
