import { Box, Checkbox, Modal, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";

import { ImportForm } from "components/common/ImportForm";
import { aironeApiClient } from "repository/AironeApiClient";

const StyledModal = styled(Modal)(({}) => ({
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
}));

const Paper = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  backgroundColor: theme.palette.background.paper,
  border: "2px solid #000",
  boxShadow: theme.shadows[5],
  padding: theme.spacing(2, 3, 1),
  width: "50%",
}));

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
    <StyledModal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      open={openImportModal}
      onClose={closeImportModal}
    >
      <Paper>
        <Typography variant={"h6"} my="8px">
          エントリのインポート
        </Typography>
        <Typography variant={"body2"} my="4px">
          インポートするファイルを選択してください。
        </Typography>
        <Typography variant={"caption"} my="4px">
          ※CSV形式のファイルは選択できません。
        </Typography>
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
              aironeApiClient.importEntries(data, forceImport)
            }
            handleCancel={closeImportModal}
          />
        </Box>
      </Paper>
    </StyledModal>
  );
};
