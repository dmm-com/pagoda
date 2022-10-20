import {
  Box,
  Checkbox,
  Divider,
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

import { GroupTreeItem } from "./GroupTreeItem";

const useStyles = makeStyles<Theme>((theme) => ({
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
  selectedGroupId: number;
  handleSelectGroupId: (groupId: number | null) => void;
}

export const GroupTreeRoot: FC<Props> = ({
  groupTrees,
  selectedGroupId,
  handleSelectGroupId,
}) => {
  const classes = useStyles();

  return (
    <Box>
      <Typography mt="16px">
        選択したいグループにチェックマークを入れてください。
      </Typography>
      <Divider sx={{ mt: "16px" }} />
      <List>
        {groupTrees.map((groupTree) => (
          <ListItem key={groupTree.id} className={classes.listItem}>
            <List>
              <ListItem>
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
                  to={groupPath(groupTree.id)}
                >
                  {groupTree.name}
                </Typography>
              </ListItem>
              {groupTree.children.length > 0 && (
                <GroupTreeItem
                  depth={1}
                  groupTrees={groupTree.children}
                  selectedGroupId={selectedGroupId}
                  handleSelectGroupId={handleSelectGroupId}
                />
              )}
            </List>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};
