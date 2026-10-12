import { Box, Typography } from "@mui/material";

export const IframeLoginCompletePage = () => (
  <Box p={3}>
    <Typography variant="h5">ログインしました</Typography>
    <Typography>
      このタブを閉じて元のページに戻り、再読み込みしてください。
    </Typography>
  </Box>
);
