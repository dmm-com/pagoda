import { Divider as MuiDivider } from "@mui/material";
import React from "react";

/*
interface Props {
    sx?: any;
}
*/

export const Divider = ({ sx = undefined }) => {
  if (sx) {
    return <MuiDivider sx={sx} />;
  } else {
    return (
      <MuiDivider
        sx={{
          my: "64px",
          height: "1px",
          backgroundColor: "rgba(0, 0, 0, 0.12)",
        }}
      />
    );
  }
};
