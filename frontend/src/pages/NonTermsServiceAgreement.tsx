import { Box, Button, Typography } from "@mui/material";
import { FC } from "react";

import { loginPath } from "../routes/Routes";

import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

export const NonTermsServiceAgreementPage: FC = () => {
  const { t } = useTranslation();
  const handleLogout = async () => {
    await aironeApiClient.postLogout();
    window.location.href = `${loginPath()}?next=${window.location.pathname}`;
  };

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
          :;(∩´﹏`∩);:
        </Typography>
      </Box>
      <Typography color="#455A64">{t("user.terms.description")}</Typography>
      <Box>
        <Button
          variant="contained"
          color="secondary"
          sx={{ borderRadius: "16px", my: "40px" }}
          onClick={() => handleLogout()}
        >
          {t("user.terms.backToAgreement")}
        </Button>
      </Box>
    </Box>
  );
};
