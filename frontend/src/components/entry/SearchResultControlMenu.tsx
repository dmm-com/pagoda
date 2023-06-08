import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import {
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import React, { FC } from "react";
import { Link, useHistory } from "react-router-dom";

import { RateLimitedClickable } from "../common/RateLimitedClickable";

import {
  aclPath,
  entityHistoryPath,
  entityPath,
  entitiesPath,
  restoreEntryPath,
  topPath,
  entityEntriesPath,
} from "Routes";
import { Confirmable } from "components/common/Confirmable";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

interface Props {
  attrName: string;
  anchorElem: HTMLButtonElement | null;
  handleClose: (name: string) => void;
}

export const SearchResultControlMenu: FC<Props> = ({
  attrName,
  anchorElem,
  handleClose,
}) => {
  return (
    <Menu
      id={attrName}
      open={Boolean(anchorElem)}
      onClose={() => handleClose(attrName)}
      anchorEl={anchorElem}
      >
      <MenuItem>
        <Typography>空白</Typography>
      </MenuItem>
      <MenuItem>
        <Typography>空白ではない</Typography>
      </MenuItem>
    </Menu>
  );
};
