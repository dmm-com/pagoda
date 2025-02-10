import { EntityList } from "@dmm-com/airone-apiclient-typescript-fetch";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Card,
  CardActionArea,
  CardContent,
  CardHeader,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { Link } from "react-router";

import { EntityControlMenu } from "./EntityControlMenu";

import { ClipboardCopyButton } from "components/common/ClipboardCopyButton";
import { EntryImportModal } from "components/entry/EntryImportModal";
import { entityEntriesPath } from "routes/Routes";

const EntityNote = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  display: "-webkit-box",
  overflow: "hidden",
  webkitBoxOrient: "vertical",
  webkitLineClamp: 2,
}));

const EntityName = styled(Typography)(({}) => ({
  textOverflow: "ellipsis",
  overflow: "hidden",
  whiteSpace: "nowrap",
}));

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

const StyledCardContent = styled(CardContent)(({}) => ({
  p: "0px",
  mt: "0px",
  mx: "16px",
  mb: "0px",
  lineHeight: 2,
}));

interface Props {
  entity: EntityList;
  setToggle?: () => void;
}

export const EntityListCard: FC<Props> = ({ entity, setToggle }) => {
  const [anchorElem, setAnchorElem] = useState<HTMLButtonElement | null>(null);
  const [openImportModal, setOpenImportModal] = React.useState(false);

  return (
    <StyledCard>
      <StyledCardHeader
        title={
          <CardActionArea component={Link} to={entityEntriesPath(entity.id)}>
            <Tooltip title={entity.name} placement="bottom-start">
              <EntityName variant="h6">{entity.name}</EntityName>
            </Tooltip>
          </CardActionArea>
        }
        action={
          <>
            <ClipboardCopyButton name={entity.name} />

            <IconButton
              onClick={(e) => {
                setAnchorElem(e.currentTarget);
              }}
            >
              <MoreVertIcon fontSize="small" />
            </IconButton>
            <EntityControlMenu
              entityId={entity.id}
              anchorElem={anchorElem}
              handleClose={() => setAnchorElem(null)}
              setOpenImportModal={setOpenImportModal}
              setToggle={setToggle}
            />
          </>
        }
      />
      <StyledCardContent>
        <EntityNote>{entity.note}</EntityNote>
      </StyledCardContent>

      <EntryImportModal
        openImportModal={openImportModal}
        closeImportModal={() => setOpenImportModal(false)}
      />
    </StyledCard>
  );
};
