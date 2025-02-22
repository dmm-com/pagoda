import { CategoryList } from "@dmm-com/airone-apiclient-typescript-fetch";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import TurnedInTwoToneIcon from "@mui/icons-material/TurnedInTwoTone";
import { Box, IconButton, Typography } from "@mui/material";
import React, { FC, useState } from "react";

import { CategoryControlMenu } from "components/category/CategoryControlMenu";
import { BetweenAlignedBox, FlexBox } from "components/common/FlexBox";

interface Props {
  category: CategoryList;
  isEdit: boolean;
  setToggle: () => void;
}

export const CategoryListHeader: FC<Props> = ({
  category,
  isEdit,
  setToggle,
}) => {
  const [categoryAnchorEl, setCategoryAnchorEl] =
    useState<HTMLButtonElement | null>(null);

  return (
    <BetweenAlignedBox>
      {/* Category image */}
      <FlexBox alignItems="center">
        <Box mr="8px" p="4px" height="24px" width="24px">
          <TurnedInTwoToneIcon sx={{ color: "#626687" }} />
        </Box>

        {/* Category title */}
        <Typography variant="h6" component="div">
          {category.name}
        </Typography>
      </FlexBox>

      {/* Category control menu */}
      {isEdit && (
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
      )}
    </BetweenAlignedBox>
  );
};
