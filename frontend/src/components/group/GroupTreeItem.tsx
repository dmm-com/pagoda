import { Checkbox, ListItem, Typography } from "@mui/material";
import React, { FC } from "react";
import { Link } from "react-router-dom";

import { groupPath } from "../../Routes";
import { GroupTree } from "../../apiclient/AironeApiClientV2";
import { DjangoContext } from "../../utils/DjangoContext";

const CHILDREN_INDENT_WIDTH = 16;

interface Props {
  depth: number;
  groupTrees: GroupTree[];
  selectedGroupId: number;
  handleSelectGroupId: (groupId: number | null) => void;
}

export const GroupTreeItem: FC<Props> = ({
  depth,
  groupTrees,
  selectedGroupId,
  handleSelectGroupId,
}) => {
  const isSuperuser = DjangoContext.getInstance().user.isSuperuser;

  return (
    <>
      {groupTrees.map((groupTree) => (
        <React.Fragment key={groupTree.id}>
          <ListItem sx={{ ml: `${depth * CHILDREN_INDENT_WIDTH}px` }}>
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
          </ListItem>
          {groupTree.children.length > 0 && (
            <GroupTreeItem
              depth={depth + 1}
              groupTrees={groupTree.children}
              selectedGroupId={selectedGroupId}
              handleSelectGroupId={handleSelectGroupId}
            />
          )}
        </React.Fragment>
      ))}
    </>
  );
};
