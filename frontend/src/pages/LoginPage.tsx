import ExitToApp from "@mui/icons-material/ExitToApp";
import InfoIcon from "@mui/icons-material/Info";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  IconButton,
  Input,
  InputAdornment,
  Link,
  TextField,
  Typography,
} from "@mui/material";
import { FC, FormEvent, useCallback, useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router";

import { PasswordResetConfirmModal } from "../components/user/PasswordResetConfirmModal";
import { PasswordResetModal } from "../components/user/PasswordResetModal";
import { aironeApiClient } from "../repository/AironeApiClient";

import { useTranslation } from "hooks/useTranslation";
import { iframeLoginCompletePath, iframePath, loginPath } from "routes/Routes";
import { ServerContext } from "services/ServerContext";

export const LoginPage: FC = () => {
  const serverContext = ServerContext.getInstance();
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  const [showPassword, setShowPassword] = useState(false);
  const [isAlert, setIsAlert] = useState(false);
  const [showAlertForTermsOfService, setShowAlertForTermsOfService] =
    useState(false);
  const [agreeWithServiceContract, setAgreeWithServiceContract] =
    useState(false);
  const [openPasswordResetModal, setOpenPasswordResetModal] = useState(false);

  // Capture the password reset parameters once on mount. They are kept in
  // state (instead of being derived from the URL) because the token is removed
  // from the location right after, to avoid leaking it via the Referer header.
  const [resetParams] = useState(() => {
    const params = new URLSearchParams(location.search);
    return {
      uidb64: params.get("uidb64") ?? "",
      token: params.get("token") ?? "",
    };
  });
  const [openPasswordResetConfirmModal, setOpenPasswordResetConfirmModal] =
    useState(() => {
      const params = new URLSearchParams(location.search);
      return params.get("uidb64") != null && params.get("token") != null;
    });

  useEffect(() => {
    const params = new URLSearchParams(location.search);

    // get token from query parameter, then delete it to avoid leaking via Referer header(a similar logic to Django auth module).
    if (params.get("token") != null) {
      params.delete("token");
      navigate(
        {
          pathname: location.pathname,
          search: "?" + params.toString(),
        },
        { replace: true },
      );
    }
  }, [location.pathname, location.search, navigate]);

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsAlert(false);

    const data = new FormData(event.currentTarget);

    // set AGREE_TERM_OF_SERVICE when user indicates to agree with Pagoda's service contract
    // when serverContext.checkTermService is true.
    if (serverContext?.checkTermService) {
      if (agreeWithServiceContract === true) {
        data.append(
          "extra_param",
          JSON.stringify({ AGREE_TERM_OF_SERVICE: true }),
        );
      } else {
        // abort login process when user does not agree with Pagoda's service contract
        setShowAlertForTermsOfService(true);
        return;
      }
    }

    const resp = await aironeApiClient.postLogin(data);
    if (resp.type === "opaqueredirect") {
      window.location.href = serverContext?.loginNext ?? "";
    } else {
      setIsAlert(true);
    }
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

  const nextUrl = new URL(
    serverContext?.loginNext || "/",
    window.location.origin,
  );
  const isIframeDestination =
    nextUrl.origin === window.location.origin &&
    (nextUrl.pathname === iframePath().replace(/\/$/, "") ||
      nextUrl.pathname.startsWith(iframePath())) &&
    nextUrl.pathname !== iframeLoginCompletePath();

  if (isIframeDestination) {
    const loginUrl = `${loginPath()}?${new URLSearchParams({
      next: iframeLoginCompletePath(),
    })}`;
    return (
      <Box p={3}>
        <Typography>AirOne にログインしてください。</Typography>
        <Button
          component="a"
          href={loginUrl}
          target="_blank"
          rel="noopener noreferrer"
          variant="contained"
        >
          別タブでログイン
        </Button>
        <Typography>ログイン後、この画面で再読み込みしてください。</Typography>
        <Button onClick={() => window.location.assign(nextUrl.href)}>
          再読み込み
        </Button>
      </Box>
    );
  }

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
          {serverContext?.title}
        </Typography>
        <Typography variant="subtitle2" mt={2}>
          {serverContext?.subTitle}
        </Typography>
        {serverContext?.checkTermService && (
          <Box width={500}>
            <FormControl>
              <FormGroup>
                <FormControlLabel
                  control={
                    <Checkbox
                      onChange={(e) => {
                        setAgreeWithServiceContract(e.target.checked);
                        setShowAlertForTermsOfService(false);
                      }}
                    />
                  }
                  label={t("user.login.agreeTerms")}
                />
                <Link href={serverContext?.termsOfServiceUrl} target="_blank">
                  {t("user.login.termsLinkLabel")}
                </Link>
              </FormGroup>
              <FormHelperText>
                {showAlertForTermsOfService && (
                  <Alert
                    severity="error"
                    onClose={() => {
                      setShowAlertForTermsOfService(false);
                    }}
                  >
                    {t("user.login.termsRequired")}
                  </Alert>
                )}
              </FormHelperText>
            </FormControl>
          </Box>
        )}
        <Box width={500} height={50} mt={2}>
          {isAlert ? (
            <Alert
              severity="error"
              onClose={() => {
                setIsAlert(false);
              }}
            >
              {t("user.login.invalidCredentials")}
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
            value={serverContext?.loginNext}
          />
          <Box display="flex" flexDirection="column" width="100%" my="8px">
            {serverContext?.singleSignOnLoginUrl != null && (
              <Link
                color="secondary"
                href={serverContext.singleSignOnLoginUrl}
                sx={{ cursor: "pointer" }}
              >
                <ExitToApp
                  sx={{
                    fontSize: "14px",
                    verticalAlign: "middle",
                  }}
                />
                <Typography fontSize="16px" ml={1} display="inline">
                  {t("user.login.ssoLogin")}
                </Typography>
              </Link>
            )}
            <Link
              color="secondary"
              sx={{ cursor: "pointer" }}
              href={serverContext?.noteLink}
            >
              <InfoIcon
                sx={{
                  fontSize: "14px",
                  verticalAlign: "middle",
                }}
              />
              <Typography fontSize="16px" ml={1} display="inline">
                {serverContext?.noteDesc}
              </Typography>
            </Link>
            {serverContext?.passwordResetDisabled ? (
              <Typography
                color="secondary"
                fontSize="16px"
                ml={1}
                display="inline"
                sx={{ textDecoration: "line-through" }}
              >
                {t("user.login.passwordReset")}
              </Typography>
            ) : (
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
                  {t("user.login.passwordReset")}
                </Typography>
              </Link>
            )}
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
        uidb64={resetParams.uidb64}
        token={resetParams.token}
      />
    </Box>
  );
};
