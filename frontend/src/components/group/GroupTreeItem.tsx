import MoreVertIcon from "@mui/icons-material/MoreVert";
import { Checkbox, IconButton, ListItem, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router";

import { GroupTree } from "../../repository/AironeApiClient";
import { groupPath } from "../../routes/Routes";
import { ServerContext } from "../../services/ServerContext";

const CHILDREN_INDENT_WIDTH = 16;

interface Props {
  depth: number;
  groupTrees: GroupTree[];
  selectedGroupId: number | null;
  handleSelectGroupId: (groupId: number | null) => void;
  setGroupAnchorEls?: (
    els: { groupId: number; el: HTMLButtonElement } | null
  ) => void;
}

export const GroupTreeItem: FC<Props> = ({
  depth,
  groupTrees,
  selectedGroupId,
  handleSelectGroupId,
  setGroupAnchorEls,
}) => {
  const isSuperuser = ServerContext.getInstance()?.user?.isSuperuser ?? false;

  return (
    <>
      {groupTrees.map((groupTree) => (
        <React.Fragment key={groupTree.id}>
          <ListItem
            sx={{
              width: "100%",
              pl: `${(depth + 1) * CHILDREN_INDENT_WIDTH}px`,
            }}
          >
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
              depth={depth + 1}
              groupTrees={groupTree.children}
              selectedGroupId={selectedGroupId}
              handleSelectGroupId={handleSelectGroupId}
              setGroupAnchorEls={setGroupAnchorEls}
            />
          )}
        </React.Fragment>
      ))}
    </>
  );
};
