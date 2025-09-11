import { Pagination, Stack, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC } from "react";

import { CenterAlignedBox } from "components/common/FlexBox";

const StyledBox = styled(CenterAlignedBox)(({}) => ({
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
    <StyledBox id="pagination">
      <Typography>
        {`${Math.min(maxRowCount * (page - 1) + 1, count)} - ${Math.min(
          maxRowCount * page,
          count,
        )} / ${count} 件`}
      </Typography>
      <Stack spacing={2}>
        <Pagination
          count={Math.ceil(count / maxRowCount)}
          page={page}
          onChange={(_, newPage) => changePage(newPage)}
          siblingCount={1}
          boundaryCount={1}
          color="primary"
        />
      </Stack>
    </StyledBox>
  );
};
