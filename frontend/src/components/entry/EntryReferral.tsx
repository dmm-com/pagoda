import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import React, { FC, useState } from "react";
import { Link } from "react-router-dom";

import { entryDetailsPath } from "Routes";
import { SearchBox } from "components/common/SearchBox";

interface Props {
  referredEntries: {
    id: number;
    name: string;
    entity: string;
  }[];
}

export const EntryReferral: FC<Props> = ({ referredEntries }) => {
  const [keyword, setKeyword] = useState("");
  const matchedEntries = referredEntries.filter((e) =>
    e.name.toLowerCase().includes(keyword.toLowerCase());
  );

  return (
    <Box className="row" id="referred_objects">
      <Box className="col">
        <Typography sx={{ fontSize: "16px" }}>
          関連づけられたエントリ(計{matchedEntries.length})
        </Typography>
        <SearchBox
          placeholder="絞り込む"
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value);
          }}
        />
        <Box className="list-group" id="referral_entries">
          <List>
            {matchedEntries.map((entry) => (
              <ListItem key={entry.id} disablePadding>
                <ListItemButton
                  component={Link}
                  to={entryDetailsPath(entry.id)}
                >
                  <ListItemText>{entry.name}</ListItemText>
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Box>
    </Box>
  );
};
