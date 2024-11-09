import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Checkbox,
  IconButton,
  List,
  ListItem,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { GroupTree } from "../../repository/AironeApiClient";
import { groupPath } from "../../routes/Routes";
import { ServerContext } from "../../services/ServerContext";

import { GroupTreeItem } from "./GroupTreeItem";

const StyledListItem = styled(ListItem)(({}) => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "white",
  },
  "&:nth-of-type(even)": {
    backgroundColor: "#607D8B0A",
  },
  padding: 0,
}));

interface Props {
  groupTrees: GroupTree[];
  selectedGroupId: number | null;
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
  const isSuperuser = ServerContext.getInstance()?.user?.isSuperuser ?? false;

  return (
    <List data-testid="GroupList">
      {groupTrees.map((groupTree) => (
        <StyledListItem key={groupTree.id}>
          <List sx={{ width: "100%" }}>
            <ListItem sx={{ width: "100%" }}>
              <Checkbox
                checked={groupTree.id === selectedGroupId}
                onChange={(e) =>
                  handleSelectGroupId(e.target.checked ? groupTree.id : null)
                }
              />
              <Typography
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
        </StyledListItem>
      ))}
    </List>
  );
};
