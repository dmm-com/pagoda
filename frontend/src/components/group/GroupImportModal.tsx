import { FC, useCallback } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const GroupImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const { t } = useTranslation();
  const handleImport = useCallback(async (data: string | ArrayBuffer) => {
    await aironeApiClient.importGroups(data);
  }, []);

  return (
    <AironeModal
      title={t("group.importModal.title")}
      description={t("group.importModal.description")}
      caption={t("group.importModal.caption")}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <ImportForm handleImport={handleImport} handleCancel={closeImportModal} />
    </AironeModal>
  );
};
