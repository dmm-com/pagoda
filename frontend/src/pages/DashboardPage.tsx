import { Container } from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";

import { CategoryList } from "components/category/CategoryList";

const StyledContainer = styled(Container)({
  marginTop: "16px",
});

export const DashboardPage: FC = () => {
  return (
    <StyledContainer>
      <CategoryList />
    </StyledContainer>
  );
};
