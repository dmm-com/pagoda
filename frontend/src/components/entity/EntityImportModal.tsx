import React, { FC, useCallback } from "react";

import { aironeApiClient } from "../../repository/AironeApiClient";
import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const EntityImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const handleImport = useCallback(async (data: string | ArrayBuffer) => {
    await aironeApiClient.importEntities(data);
  }, []);

  return (
    <AironeModal
      title={"モデルのインポート"}
      description={"インポートするファイルを選択してください。"}
      caption={"※CSV形式のファイルは選択できません。"}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <ImportForm handleImport={handleImport} handleCancel={closeImportModal} />
    </AironeModal>
  );
};
