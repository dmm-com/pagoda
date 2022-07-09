import { Box, Divider, Typography, Theme } from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC, ReactElement } from "react";

const useStyles = makeStyles<Theme>((theme) => ({
  frame: {
    width: "100%",
    height: "284px",
  },
  fixed: {
    position: "fixed",
    zIndex: 2,
    width: "100%",
    backgroundColor: "white",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
  },
  headerTop: {
    width: theme.breakpoints.values.lg,
    height: "88px",
    marginTop: "124px",
    display: "flex",
  },
  headerBottom: {
    width: theme.breakpoints.values.lg,
    height: "40px",
    display: "flex",
    alignItems: "flex-end",
  },
  titleBox: {
    display: "flex",
    alignItems: "flex-end",
    margin: "8px 0",
  },
  title: {
    height: "72px",
    maxWidth: "700px",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
}));

interface Props {
  title: string;
  subTitle?: string;
  description?: string;
  componentSubmits: ReactElement<any>;
  componentControl?: ReactElement<any>;
}

export const PageHeader: FC<Props> = ({
  title,
  subTitle,
  description,
  componentControl,
  componentSubmits,
}) => {
  const classes = useStyles();

  return (
    <Box className={classes.frame}>
      <Box className={classes.fixed}>
        <Box className={classes.headerTop}>
          <Box className={classes.titleBox}>
            <Typography variant="h2" mr="64px" className={classes.title}>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight="300">
              {subTitle}
            </Typography>
          </Box>
          <Box ml="auto">{componentControl}</Box>
        </Box>
        <Box className={classes.headerBottom}>
          <Typography>{description}</Typography>
          <Box ml="auto">{componentSubmits}</Box>
        </Box>
        <Divider flexItem sx={{ mt: "32px", borderColor: "black" }} />
      </Box>
    </Box>
  );
};
