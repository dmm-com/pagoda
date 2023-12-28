import { Box, Pagination, Stack, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

const StyledBox = styled(Box)(({}) => ({
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  margin: "30px 0",
}));

interface Props {
  count: number;
  maxRowCount: number;
  page: number;
  changePage: (page: number) => void;
}

export const PaginationFooter: FC<Props> = ({
  count,
  maxRowCount,
  page,
  changePage,
}) => {
  return (
    <StyledBox>
      <Typography>
        {`${Math.min(maxRowCount * (page - 1) + 1, count)} - ${Math.min(
          maxRowCount * page,
          count
        )} / ${count} 件`}
      </Typography>
      <Stack spacing={2}>
        <Pagination
          count={Math.ceil(count / maxRowCount)}
          page={page}
          onChange={(_, newPage) => changePage(newPage)}
          color="primary"
        />
      </Stack>
    </StyledBox>
  );
};
