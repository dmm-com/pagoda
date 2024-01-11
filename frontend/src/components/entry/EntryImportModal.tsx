import { Box, Checkbox, Typography } from "@mui/material";
import React, { FC, useState } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const EntryImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const [forceImport, setForceImport] = useState(false);

  return (
    <AironeModal
      title={"エントリのインポート"}
      description={"インポートするファイルを選択してください。"}
      caption={"※CSV形式のファイルは選択できません。"}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <Box display="flex" alignItems="center">
        <Checkbox
          checked={forceImport}
          onChange={(event) => setForceImport(event.target.checked)}
        />
        <Typography variant={"body2"}>
          強制的にインポートする(短期間にインポートを繰り返したい場合に使用してください)
        </Typography>
      </Box>
      <Box my="8px">
        <ImportForm
          handleImport={(data: string | ArrayBuffer) =>
            aironeApiClientV2.importEntries(data, forceImport)
          }
          handleCancel={closeImportModal}
        />
      </Box>
    </AironeModal>
  );
};
