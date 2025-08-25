import { Box, Button, Typography } from "@mui/material";
import { FC, useCallback } from "react";

import { topPath } from "../../routes/Routes";

interface ErrorPageBaseProps {
  title: string;
  description: string[];
}

export const ErrorPageBase: FC<ErrorPageBaseProps> = ({
  title,
  description,
}) => {
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
          {title}
        </Typography>
      </Box>
      <Box display="flex" flexDirection="column" alignItems="center">
        {description.map((text, index) => (
          <Typography key={index} color="#455A64">
            {text}
          </Typography>
        ))}
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
