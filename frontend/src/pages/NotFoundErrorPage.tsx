import { Box, Button, Typography } from "@mui/material";
import React, { FC, useCallback } from "react";

import { topPath } from "../Routes";

export const NotFoundErrorPage: FC = () => {
  const handleClickGoToTop = useCallback(() => {
    location.href = topPath();
  }, []);

  return (
    <Box
      display="flex"
      flexDirection="column"
      flexGrow={1}
      alignItems="center"
      justifyContent="center"
    >
      <Box display="flex" my="52px">
        <Typography variant="h1" color="#B0BEC5" fontWeight="bold">
          404
        </Typography>
        <Typography variant="h1" color="#B0BEC5" fontWeight="bold">
          　|ω·`)
        </Typography>
      </Box>
      <Typography color="#455A64">
        アクセスしたページは削除、変更されたか、現在利用できない可能性があります。
      </Typography>
      <Box>
        <Button
          variant="contained"
          color="secondary"
          sx={{ borderRadius: "16px", my: "40px" }}
          onClick={handleClickGoToTop}
        >
          トップページへ
        </Button>
      </Box>
    </Box>
  );
};
