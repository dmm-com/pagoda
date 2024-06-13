import { Box, Button, Typography } from "@mui/material";
import React, { FC, useCallback } from "react";

import { topPath } from "../Routes";

export const UnavailableErrorPage: FC = () => {
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
        <Typography
          id="sorry_forbidden"
          variant="h1"
          color="#B0BEC5"
          fontWeight="bold"
        >
          利用できません:;(∩´﹏`∩);:
        </Typography>
      </Box>
      <Box display="flex" flexDirection="column" alignItems="center">
        <Typography color="#455A64">
          このページは現在、利用ができません。
        </Typography>
        <Typography color="#455A64">
          管理者からのお知らせをご覧いただくか、お問合せください。
        </Typography>
      </Box>
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

