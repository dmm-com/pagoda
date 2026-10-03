import { useSnackbar } from "notistack";
import { FC, useCallback, useEffect } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const RoleImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    if (sessionStorage.getItem("role-import-success") === "1") {
      sessionStorage.removeItem("role-import-success");
      enqueueSnackbar(t("role.importModal.accepted"), {
        variant: "success",
      });
    }
  }, [enqueueSnackbar, t]);

  const handleImport = useCallback(async (data: string | ArrayBuffer) => {
    await aironeApiClient.importRoles(data);
  }, []);

  return (
    <AironeModal
      title={t("role.importModal.title")}
      description={t("role.importModal.description")}
      caption={t("role.importModal.caption")}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <ImportForm handleImport={handleImport} handleCancel={closeImportModal} />
    </AironeModal>
  );
};
