import MoreVertIcon from "@mui/icons-material/MoreVert";

import { BetweenAlignedBox } from "components/common/FlexBox";
import { CategoryControlMenu } from "components/category/CategoryControlMenu";
import React, { FC, useState } from "react";

import {
  Typography,
  IconButton,
} from "@mui/material";
import { CategoryList } from "@dmm-com/airone-apiclient-typescript-fetch";

interface Props {
  category: CategoryList;
  setOpenImportModal: (isOpened: boolean) => void;
  setToggle?: () => void;
}

export const CategoryListHeader: FC<Props> = ({
  category,
  setOpenImportModal,
  setToggle,
}) => {
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
          setOpenImportModal={setOpenImportModal}
          setToggle={setToggle}
        />
      </>
    </BetweenAlignedBox>
  );
}