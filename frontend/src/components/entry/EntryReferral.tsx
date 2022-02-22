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
    e.name.toLowerCase().includes(keyword.toLowerCase())
  );

  return (
    <Box>
      <Box px="16px">
        <Typography sx={{ fontSize: "16px", fontWeight: "Medium", pb: "16px" }}>
          関連づけられたエントリ(計{matchedEntries.length})
        </Typography>
        <SearchBox
          placeholder="エントリを絞り込む"
          value={keyword}
          onChange={(e) => {
            setKeyword(e.target.value);
          }}
        />
      </Box>
      <List sx={{ py: "32px" }}>
        {matchedEntries.map((entry) => (
          <ListItem
            key={entry.id}
            divider={true}
            disablePadding
            sx={{
              "&:first-of-type": {
                borderTop: "1px solid",
                borderTopColor: "divider",
              },
            }}
          >
            <ListItemButton component={Link} to={entryDetailsPath(entry.id)}>
              <ListItemText sx={{ px: "16px" }}>{entry.name}</ListItemText>
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );
};
