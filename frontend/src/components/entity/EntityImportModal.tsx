import React, { FC, useCallback } from "react";

import { aironeApiClientV2 } from "../../repository/AironeApiClientV2";
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
    await aironeApiClientV2.importEntities(data);
  }, []);

  return (
    <AironeModal
      title={"エンティティのインポート"}
      description={"インポートするファイルを選択してください。"}
      caption={"※CSV形式のファイルは選択できません。"}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <ImportForm handleImport={handleImport} handleCancel={closeImportModal} />
    </AironeModal>
  );
};
