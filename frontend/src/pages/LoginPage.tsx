import InfoIcon from "@mui/icons-material/Info";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import {
  Alert,
  Box,
  Button,
  IconButton,
  Input,
  InputAdornment,
  Link,
  TextField,
  Typography,
} from "@mui/material";
import React, { FC } from "react";

import { postLogin } from "utils/AironeAPIClient";
import { DjangoContext } from "utils/DjangoContext";

export const LoginPage: FC = () => {
  const djangoContext = DjangoContext.getInstance();
  const [showPassword, setShowPassword] = React.useState(false);
  const [isAlert, setIsAlert] = React.useState(false);

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsAlert(false);
    const data = new FormData(event.currentTarget);
    postLogin(data).then((resp) => {
      if (resp.type === "opaqueredirect") {
        window.location.href = djangoContext.loginNext;
      } else {
        setIsAlert(true);
      }
    });
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      bgcolor="primary.main"
      height="100vh"
    >
      <Box
        width="60%"
        minWidth="600px"
        height="70%"
        minHeight="500px"
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        bgcolor="white"
      >
        <Typography variant="h1" fontWeight={400}>
          {djangoContext.title}
        </Typography>
        <Typography variant="subtitle2" mt={2}>
          {djangoContext.subTitle}
        </Typography>
        <Box width={500} height={50} mt={2}>
          {isAlert ? (
            <Alert
              severity="error"
              onClose={() => {
                setIsAlert(false);
              }}
            >
              ユーザ名またはパスワードが違います。
            </Alert>
          ) : (
            ""
          )}
        </Box>
        <Box
          component="form"
          onSubmit={handleSubmit}
          width={500}
          display="flex"
          flexDirection="column"
          alignItems="center"
        >
          <TextField
            id="username"
            name="username"
            label="Username"
            fullWidth={true}
            margin="dense"
          />
          <TextField
            id="password"
            name="password"
            label="Password"
            type={showPassword ? "text" : "password"}
            fullWidth={true}
            margin="dense"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={handleClickShowPassword} edge="end">
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <Input
            id="next"
            name="next"
            type="hidden"
            value={djangoContext.loginNext}
          />
          {/* TODO change href url*/}
          <Link
            color="secondary"
            ml="auto"
            href={djangoContext.noteLink}
            target="_blank"
            rel="noopener pnoreferrer"
          >
            <InfoIcon
              sx={{
                fontSize: "14px",
                verticalAlign: "middle",
              }}
            />
            <Typography fontSize="12px" ml={1} display="inline">
              {djangoContext.noteDesc}
            </Typography>
          </Link>
          <Button
            type="submit"
            variant="contained"
            sx={{ mt: 7, width: "auto", py: 0.5, letterSpacing: 1.25 }}
          >
            Login
          </Button>
        </Box>
      </Box>
    </Box>
  );
};
