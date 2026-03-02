import RestoreIcon from "@mui/icons-material/Restore";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardHeader,
  IconButton,
  Modal,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import Grid from "@mui/material/Grid2";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import { FC, Suspense, useState } from "react";
import { useNavigate } from "react-router";

import { EntryAttributes } from "./EntryAttributes";

import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { usePage } from "hooks/usePage";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { aironeApiClient } from "repository/AironeApiClient";
import { restoreEntryPath, topPath } from "routes/Routes";
import { EntryListParam } from "services/Constants";
import { formatDateTime } from "services/DateUtil";
import { normalizeToMatch } from "services/StringUtil";

const StyledCard = styled(Card)(({}) => ({
  height: "100%",
}));

const StyledCardHeader = styled(CardHeader)(({}) => ({
  p: "0px",
  mt: "24px",
  mx: "16px",
  mb: "16px",
}));

const EntryName = styled(Typography)(({}) => ({
  width: "300px",
  textOverflow: "ellipsis",
  overflow: "hidden",
  whiteSpace: "nowrap",
}));

const StyledModal = styled(Modal)(({}) => ({
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
}));

const PaperBox = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  backgroundColor: theme.palette.background.paper,
  border: "2px solid #000",
  boxShadow: theme.shadows[5],
  padding: theme.spacing(2, 3, 1),
  width: theme.breakpoints.values.lg,
  height: "80%",
}));

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
}));

const HeaderTableCell = styled(TableCell)(({ theme }) => ({
  color: theme.palette.primary.contrastText,
  boxSizing: "border-box",
}));

const ItemNameTableCell = styled(TableCell)(() => ({
  width: "200px",
  wordBreak: "break-word",
}));

const ItemValueTableCell = styled(TableCell)(() => ({
  width: "950px",
  wordBreak: "break-word",
}));

const EntryDetailModalContent: FC<{
  entryId: number;
  onRestore: (entryId: number) => void;
  onClose: () => void;
}> = ({ entryId, onRestore, onClose }) => {
  const { data: entryDetail } = usePagodaSWR(
    ["entry", entryId],
    () => aironeApiClient.getEntry(entryId),
    { suspense: true },
  );

  return (
    <>
      <Typography color="primary" my={2}>
        Operation Information
      </Typography>
      <TableContainer component={Paper} style={{ overflowX: "unset" }}>
        <Table id="table_info_list">
          <TableHead sx={{ backgroundColor: "primary.dark" }}>
            <TableRow>
              <HeaderTableCell>項目</HeaderTableCell>
              <HeaderTableCell>内容</HeaderTableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <StyledTableRow>
              <ItemNameTableCell>Deleted by</ItemNameTableCell>
              <ItemValueTableCell>
                {entryDetail.deletedUser?.username}
              </ItemValueTableCell>
            </StyledTableRow>
            <StyledTableRow>
              <ItemNameTableCell>Deleted at</ItemNameTableCell>
              <ItemValueTableCell>
                {entryDetail.deletedTime != null
                  ? formatDateTime(entryDetail.deletedTime)
                  : null}
              </ItemValueTableCell>
            </StyledTableRow>
          </TableBody>
        </Table>
      </TableContainer>
      <Typography color="primary" my={2}>
        Attributes & Values
      </Typography>
      {entryDetail.attrs != null && (
        <EntryAttributes attributes={entryDetail.attrs} />
      )}
      <Box display="flex" justifyContent="flex-end" my={2}>
        <Confirmable
          componentGenerator={(handleOpen) => (
            <Button
              variant="contained"
              color="secondary"
              sx={{ margin: "0 4px" }}
              onClick={handleOpen}
            >
              復旧
            </Button>
          )}
          dialogTitle="本当に復旧しますか？"
          onClickYes={() => onRestore(entryDetail.id)}
        />
        <Button variant="outlined" sx={{ margin: "0 4px" }} onClick={onClose}>
          キャンセル
        </Button>
      </Box>
    </>
  );
};

interface Props {
  entityId: number;
}

const RestorableEntryListContent: FC<Props> = ({ entityId }) => {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const { page, query, changePage, changeQuery } = usePage();

  const [openModal, setOpenModal] = useState(false);
  const [selectedEntryId, setSelectedEntryId] = useState<number>();

  const { data: entries } = usePagodaSWR(
    ["entries", entityId, false, page, query],
    () => aironeApiClient.getEntries(entityId, false, page, query),
    { suspense: true },
  );

  const handleChangeQuery = changeQuery;

  const handleRestore = async (entryId: number) => {
    await aironeApiClient
      .restoreEntry(entryId)
      .then(() => {
        enqueueSnackbar("アイテムの復旧が完了しました", {
          variant: "success",
        });
        navigate(topPath());
        navigate(restoreEntryPath(entityId, query));
      })
      .catch(() => {
        enqueueSnackbar("アイテムの復旧が失敗しました", {
          variant: "error",
        });
      });
  };

  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width="600px">
          <SearchBox
            placeholder="アイテムを絞り込む"
            defaultValue={query}
            onKeyPress={(e) => {
              e.key === "Enter" &&
                handleChangeQuery(
                  normalizeToMatch((e.target as HTMLInputElement).value ?? ""),
                );
            }}
          />
        </Box>
      </Box>

      {/* This box shows each entry Cards */}
      <Grid container spacing={2} id="entry_list">
        {entries.results?.map((entry) => {
          return (
            <Grid size={4} key={entry.id}>
              <StyledCard>
                <StyledCardHeader
                  title={
                    <CardActionArea
                      onClick={() => {
                        setSelectedEntryId(entry.id);
                        setOpenModal(true);
                      }}
                    >
                      <EntryName variant="h6">
                        {entry.name.replace(/_deleted_.*/, "")}
                      </EntryName>
                    </CardActionArea>
                  }
                  action={
                    <>
                      <Confirmable
                        componentGenerator={(handleOpen) => (
                          <IconButton onClick={handleOpen}>
                            <RestoreIcon />
                          </IconButton>
                        )}
                        dialogTitle="本当に復旧しますか？"
                        onClickYes={() => handleRestore(entry.id)}
                      />
                    </>
                  }
                />
              </StyledCard>
            </Grid>
          );
        })}
      </Grid>
      <PaginationFooter
        count={entries.count ?? 0}
        maxRowCount={EntryListParam.MAX_ROW_COUNT}
        page={page}
        changePage={changePage}
      />
      <StyledModal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        open={openModal}
        onClose={() => setOpenModal(false)}
      >
        <PaperBox>
          {selectedEntryId != null && (
            <Suspense fallback={<Loading />}>
              <EntryDetailModalContent
                entryId={selectedEntryId}
                onRestore={handleRestore}
                onClose={() => setOpenModal(false)}
              />
            </Suspense>
          )}
        </PaperBox>
      </StyledModal>
    </Box>
  );
};

export const RestorableEntryList: FC<Props> = ({ entityId }) => {
  return (
    <Suspense fallback={<Loading />}>
      <RestorableEntryListContent entityId={entityId} />
    </Suspense>
  );
};
