import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Card,
  CardActionArea,
  CardHeader,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { FC, useState } from "react";
import { Link } from "react-router";

import { EntryBase } from "@dmm-com/airone-apiclient-typescript-fetch";
import { ClipboardCopyButton } from "components/common/ClipboardCopyButton";
import { EntryControlMenu } from "components/entry/EntryControlMenu";
import { entryDetailsPath } from "routes/Routes";

const StyledCard = styled(Card)(({}) => ({
  height: "100%",
}));

const StyledCardHeader = styled(CardHeader)(({}) => ({
  p: "0px",
  mt: "24px",
  mx: "16px",
  mb: "16px",
  ".MuiCardHeader-content": {
    width: "80%",
  },
}));

const EntryName = styled(Typography)(({}) => ({
  textOverflow: "ellipsis",
  overflow: "hidden",
  whiteSpace: "nowrap",
}));

interface Props {
  entityId: number;
  entry: EntryBase;
  setToggle?: () => void;
}

export const EntryListCard: FC<Props> = ({ entityId, entry, setToggle }) => {
  const [anchorElem, setAnchorElem] = useState<HTMLButtonElement | null>(null);

  return (
    <StyledCard>
      <StyledCardHeader
        title={
          <CardActionArea
            component={Link}
            to={entryDetailsPath(entityId, entry.id)}
          >
            <Tooltip title={entry.name} placement="bottom-start">
              <EntryName variant="h6">{entry.name}</EntryName>
            </Tooltip>
          </CardActionArea>
        }
        action={
          <>
            <ClipboardCopyButton name={entry.name} />

            <Tooltip title="アイテムの操作">
              <IconButton onClick={(e) => setAnchorElem(e.currentTarget)}>
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <EntryControlMenu
              entityId={entityId}
              entryId={entry.id}
              anchorElem={anchorElem}
              handleClose={() => setAnchorElem(null)}
              setToggle={setToggle}
            />
          </>
        }
      />
    </StyledCard>
  );
};
