import { Box, Button, Typography } from "@mui/material";
import { FC, useCallback } from "react";

import { useTranslation } from "../hooks/useTranslation";
import { topPath } from "../routes/Routes";

export const NotFoundErrorPage: FC = () => {
  const { t } = useTranslation();
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
          id="sorry_notfound"
          variant="h1"
          color="#B0BEC5"
          fontWeight="bold"
        >
          404 |ω·`)
        </Typography>
      </Box>
      <Typography color="#455A64">
        {t("errorPage.notFound.description")}
      </Typography>
      <Box>
        <Button
          variant="contained"
          color="secondary"
          sx={{ borderRadius: "16px", my: "40px" }}
          onClick={handleClickGoToTop}
        >
          {t("common.backToTop")}
        </Button>
      </Box>
    </Box>
  );
};
