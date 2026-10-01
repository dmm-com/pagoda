import { Box, Checkbox, Typography } from "@mui/material";
import { FC, useCallback, useState } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { useTranslation } from "hooks/useTranslation";
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
  const { t } = useTranslation();
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
      title={t("entry.import.title")}
      description={t("entry.import.description")}
      caption={t("entry.import.caption")}
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
          {t("entry.import.forceLabel")}
        </Typography>
      </Box>
      <Box my="8px">
        <ImportForm
          handleImport={(data: string | ArrayBuffer, previewJobIds: number[]) =>
            // Passing the approved preview lets the import leave alone anything
            // someone else changed since it was built.
            aironeApiClient.importEntries(data, forceImport, previewJobIds[0])
          }
          handleCancel={closeImportModal}
          handlePreview={handlePreview}
        />
      </Box>
    </AironeModal>
  );
};
