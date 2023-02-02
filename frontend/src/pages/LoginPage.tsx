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
import React, { FC, useCallback, useEffect, useState } from "react";
import { useHistory } from "react-router-dom";

import { PasswordResetConfirmModal } from "../components/user/PasswordResetConfirmModal";
import { PasswordResetModal } from "../components/user/PasswordResetModal";

import { postLogin } from "utils/AironeAPIClient";
import { DjangoContext } from "utils/DjangoContext";

export const LoginPage: FC = () => {
  const djangoContext = DjangoContext.getInstance();
  const history = useHistory();

  const [showPassword, setShowPassword] = useState(false);
  const [isAlert, setIsAlert] = useState(false);
  const [openPasswordResetModal, setOpenPasswordResetModal] = useState(false);
  const [uidb64, setUidb64] = useState<string>("");
  const [token, setToken] = useState<string>("");
  const [openPasswordResetConfirmModal, setOpenPasswordResetConfirmModal] =
    useState(false);

  useEffect(() => {
    const params = new URLSearchParams(location.search);

    const _uidb64 = params.get("uidb64");
    if (_uidb64 != null) {
      setUidb64(_uidb64);
    }

    // get token from query parameter, then delete it to avoid leaking via Referer header(a similar logic to Django auth module).
    const _token = params.get("token");
    if (_token != null) {
      setToken(_token);
      params.delete("token");
      history.replace({
        pathname: location.pathname,
        search: "?" + params.toString(),
      });
    }

    if (_uidb64 != null && _token != null) {
      setOpenPasswordResetConfirmModal(true);
    }
  }, [location.search]);

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsAlert(false);
    const data = new FormData(event.currentTarget);
    postLogin(data).then((resp) => {
      if (resp.type === "opaqueredirect") {
        window.location.href = djangoContext?.loginNext ?? "";
      } else {
        setIsAlert(true);
      }
    });
  };

  const handleOpenPasswordResetModal = useCallback(() => {
    setOpenPasswordResetModal(true);
  }, [setOpenPasswordResetModal]);

  const handleClosePasswordResetModal = useCallback(() => {
    setOpenPasswordResetModal(false);
  }, [setOpenPasswordResetModal]);

  const handleClosePasswordResetConfirmModal = useCallback(() => {
    setOpenPasswordResetConfirmModal(false);
  }, [setOpenPasswordResetConfirmModal]);

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
          {djangoContext?.title}
        </Typography>
        <Typography variant="subtitle2" mt={2}>
          {djangoContext?.subTitle}
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
            value={djangoContext?.loginNext}
          />
          <Box display="flex" flexDirection="column" width="100%" my="8px">
            <Link
              color="secondary"
              sx={{ cursor: "pointer" }}
              href={djangoContext?.noteLink}
            >
              <InfoIcon
                sx={{
                  fontSize: "14px",
                  verticalAlign: "middle",
                }}
              />
              <Typography fontSize="16px" ml={1} display="inline">
                {djangoContext?.noteDesc}
              </Typography>
            </Link>
            <Link
              color="secondary"
              onClick={handleOpenPasswordResetModal}
              sx={{ cursor: "pointer" }}
            >
              <InfoIcon
                sx={{
                  fontSize: "14px",
                  verticalAlign: "middle",
                }}
              />
              <Typography fontSize="16px" ml={1} display="inline">
                パスワードリセット
              </Typography>
            </Link>
          </Box>
          <Button
            type="submit"
            variant="contained"
            sx={{ mt: 7, width: "auto", py: 0.5, letterSpacing: 1.25 }}
          >
            Login
          </Button>
        </Box>
      </Box>

      <PasswordResetModal
        openModal={openPasswordResetModal}
        closeModal={handleClosePasswordResetModal}
      />
      <PasswordResetConfirmModal
        openModal={openPasswordResetConfirmModal}
        closeModal={handleClosePasswordResetConfirmModal}
        uidb64={uidb64}
        token={token}
      />
    </Box>
  );
};
