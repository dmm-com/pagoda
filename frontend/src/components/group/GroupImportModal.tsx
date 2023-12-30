import { Box, Modal, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useCallback } from "react";

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

export const GroupImportModal: FC<Props> = ({
  openImportModal,
  closeImportModal,
}) => {
  const handleImport = useCallback(async (data: string | ArrayBuffer) => {
    await aironeApiClient.importGroups(data);
  }, []);

  return (
    <StyledModal
      aria-labelledby="transition-modal-title"
      aria-describedby="transition-modal-description"
      open={openImportModal}
      onClose={closeImportModal}
    >
      <Paper>
        <Typography variant={"h6"} my="8px">
          グループのインポート
        </Typography>
        <Typography variant={"body2"} my="4px">
          インポートするファイルを選択してください。
        </Typography>
        <Typography variant={"caption"} my="4px">
          ※CSV形式のファイルは選択できません。
        </Typography>
        <ImportForm
          handleImport={handleImport}
          handleCancel={closeImportModal}
        />
      </Paper>
    </StyledModal>
  );
};
