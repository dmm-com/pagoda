import { Box, Checkbox, Typography } from "@mui/material";
import { FC, useCallback, useState } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { aironeApiClient } from "repository/AironeApiClient";
import { ImportPreviewFailure } from "services/ImportPreviewJob";

interface Props {
  openImportModal: boolean;
  closeImportModal: () => void;
}

export const EntryImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const [forceImport, setForceImport] = useState(false);

  const handlePreview = useCallback(async (data: string | ArrayBuffer) => {
    const { jobIds, errors } =
      await aironeApiClient.startImportEntriesPreview(data);
    if (jobIds.length === 0) {
      // Nothing can be previewed: every model in the file was rejected.
      throw new ImportPreviewFailure(
        errors.join(" / ") || "プレビューできるモデルがありませんでした",
      );
    }
    return jobIds;
  }, []);

  return (
    <AironeModal
      title={"アイテムのインポート"}
      description={"インポートするファイルを選択してください。"}
      caption={"※CSV形式のファイルは選択できません。"}
      open={openImportModal}
      onClose={closeImportModal}
    >
      <Box display="flex" alignItems="center">
        <Checkbox
          inputProps={
            {
              "data-testid": "force-import",
            } as React.InputHTMLAttributes<HTMLInputElement>
          }
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
            aironeApiClient.importEntries(data, forceImport)
          }
          handleCancel={closeImportModal}
          handlePreview={handlePreview}
        />
      </Box>
    </AironeModal>
  );
};
