import { Box, Checkbox, Typography } from "@mui/material";
import { FC, useState } from "react";

import { AironeModal } from "../common/AironeModal";

import { ImportForm } from "components/common/ImportForm";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

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
          checked={forceImport}
          onChange={(event) => setForceImport(event.target.checked)}
        />
        <Typography variant={"body2"}>
          {t("entry.import.forceLabel")}
        </Typography>
      </Box>
      <Box my="8px">
        <ImportForm
          handleImport={(data: string | ArrayBuffer) =>
            aironeApiClient.importEntries(data, forceImport)
          }
          handleCancel={closeImportModal}
        />
      </Box>
    </AironeModal>
  );
};
