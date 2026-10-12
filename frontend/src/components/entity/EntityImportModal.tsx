import { FC, useCallback } from "react";

import { aironeApiClient } from "../../repository/AironeApiClient";
import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { useTranslation } from "hooks/useTranslation";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const EntityImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const { t } = useTranslation();

  const handleImport = useCallback(async (data: string | ArrayBuffer) => {
    await aironeApiClient.importEntities(data);
  }, []);

  const handlePreview = useCallback(
    async (data: string | ArrayBuffer) => [
      await aironeApiClient.startImportEntitiesPreview(data),
    ],
    [],
  );

  return (
    <AironeModal
      title={t("entity.import.title")}
      description={t("entity.import.description")}
      caption={t("entity.import.caption")}
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
