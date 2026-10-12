import { FC, useCallback } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const UserImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const { t } = useTranslation();
  const handleImport = useCallback(async (data: string | ArrayBuffer) => {
    await aironeApiClient.importUsers(data);
  }, []);

  return (
    <AironeModal
      title={t("user.importModal.title")}
      description={t("user.importModal.description")}
      caption={t("user.importModal.caption")}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <ImportForm handleImport={handleImport} handleCancel={closeImportModal} />
    </AironeModal>
  );
};
