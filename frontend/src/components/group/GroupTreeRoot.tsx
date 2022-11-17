import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Box,
  Checkbox,
  IconButton,
  List,
  ListItem,
  Theme,
  Typography,
} from "@mui/material";
import { makeStyles } from "@mui/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { groupPath } from "../../Routes";
import { GroupTree } from "../../apiclient/AironeApiClientV2";
import { DjangoContext } from "../../utils/DjangoContext";

import { GroupTreeItem } from "./GroupTreeItem";

const useStyles = makeStyles<Theme>(() => ({
  listItem: {
    "&:nth-of-type(odd)": {
      backgroundColor: "white",
    },
    "&:nth-of-type(even)": {
      backgroundColor: "#607D8B0A",
    },
  },
}));

interface Props {
  groupTrees: GroupTree[];
  selectedGroupId?: number;
  handleSelectGroupId: (groupId: number | null) => void;
  setGroupAnchorEls?: (
    els: { groupId: number; el: HTMLButtonElement } | null
  ) => void;
}

export const GroupTreeRoot: FC<Props> = ({
  groupTrees,
  selectedGroupId,
  handleSelectGroupId,
  setGroupAnchorEls,
}) => {
  const classes = useStyles();
  const isSuperuser = DjangoContext.getInstance().user.isSuperuser;

  return (
    <Box>
      <List>
        {groupTrees.map((groupTree) => (
          <ListItem key={groupTree.id} className={classes.listItem}>
            <List sx={{ width: "100%" }}>
              <ListItem sx={{ width: "100%" }}>
                <Checkbox
                  checked={groupTree.id === selectedGroupId}
                  onChange={(e) =>
                    handleSelectGroupId(e.target.checked ? groupTree.id : null)
                  }
                />
                <Typography
                  variant="h5"
                  my="8px"
                  component={Link}
                  to={isSuperuser ? groupPath(groupTree.id) : "#"}
                >
                  {groupTree.name}
                </Typography>
                {setGroupAnchorEls != null && (
                  <IconButton
                    sx={{ margin: "0 0 0 auto" }}
                    onClick={(e) => {
                      setGroupAnchorEls({
                        groupId: groupTree.id,
                        el: e.currentTarget,
                      });
                    }}
                  >
                    <MoreVertIcon />
                  </IconButton>
                )}
              </ListItem>
              {groupTree.children.length > 0 && (
                <GroupTreeItem
                  depth={1}
                  groupTrees={groupTree.children}
                  selectedGroupId={selectedGroupId}
                  handleSelectGroupId={handleSelectGroupId}
                  setGroupAnchorEls={setGroupAnchorEls}
                />
              )}
            </List>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};
