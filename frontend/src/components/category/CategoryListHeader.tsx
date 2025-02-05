import { CategoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { IconButton, Typography } from "@mui/material";
import React, { FC, useState } from "react";

import { CategoryControlMenu } from "components/category/CategoryControlMenu";
import { BetweenAlignedBox } from "components/common/FlexBox";

interface Props {
  category: CategoryList;
  setToggle?: () => void;
}

export const CategoryListHeader: FC<Props> = ({ category, setToggle }) => {
  const [categoryAnchorEl, setCategoryAnchorEl] =
    useState<HTMLButtonElement | null>(null);

  return (
    <BetweenAlignedBox>
      {/* Category title */}
      <Typography variant="h6" component="div">
        {category.name}
      </Typography>

      {/* Category control menu */}
      <>
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
      </>
    </BetweenAlignedBox>
  );
};
