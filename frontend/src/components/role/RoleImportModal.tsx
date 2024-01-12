import React, { FC, useCallback } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { aironeApiClient } from "repository/AironeApiClient";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const RoleImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const handleImport = useCallback(async (data: string | ArrayBuffer) => {
    await aironeApiClient.importRoles(data);
  }, []);

  return (
    <AironeModal
      title={"ロールのインポート"}
      description={"インポートするファイルを選択してください。"}
      caption={"※CSV形式のファイルは選択できません。"}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <ImportForm handleImport={handleImport} handleCancel={closeImportModal} />
    </AironeModal>
  );
};
