import React, { FC, useCallback } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const RoleImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const handleImport = useCallback(async (data: string | ArrayBuffer) => {
    await aironeApiClientV2.importRoles(data);
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
