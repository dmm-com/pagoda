import { Box, Button, Typography } from "@mui/material";
import React, { FC, useCallback } from "react";

import { topPath } from "../routes/Routes";

export const ForbiddenErrorPage: FC = () => {
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
          権限がありません… (|| ﾟДﾟ)
        </Typography>
      </Box>
      <Box display="flex" flexDirection="column" alignItems="center">
        <Typography color="#455A64">
          あなたはこのページを閲覧する権限を持っていません。
        </Typography>
        <Typography color="#455A64">
          ページの管理者がアクセス権を付与できる可能性があります。
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
