import { CategoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { Box, IconButton, Typography } from "@mui/material";
import React, { FC, useState } from "react";

import { CategoryControlMenu } from "components/category/CategoryControlMenu";
import { BetweenAlignedBox, FlexBox } from "components/common/FlexBox";

interface Props {
  category: CategoryList;
  setToggle?: () => void;
}

export const CategoryListHeader: FC<Props> = ({ category, setToggle }) => {
  const [categoryAnchorEl, setCategoryAnchorEl] =
    useState<HTMLButtonElement | null>(null);

  return (
    <BetweenAlignedBox>
      {/* Category image */}
      <FlexBox>
        <Box
          mr={"8px"}
          sx={{ height: "24px", wdith: "24px" }}
          component="img"
          src="/static/images/category/01.png"
        />

        {/* Category title */}
        <Typography variant="h6" component="div">
          {category.name}
        </Typography>
      </FlexBox>

      {/* Category control menu */}
      <FlexBox sx={{ marginInlineStart: "40px" }}>
        <IconButton
          onClick={(e) => {
            setCategoryAnchorEl(e.currentTarget);
          }}
        >
          <MoreVertIcon fontSize="small" />
        </IconButton>
        <CategoryControlMenu
          categoryId={category.id}
          anchorElem={categoryAnchorEl}
          handleClose={() => setCategoryAnchorEl(null)}
          setToggle={setToggle}
        />
      </FlexBox>
    </BetweenAlignedBox>
  );
};
