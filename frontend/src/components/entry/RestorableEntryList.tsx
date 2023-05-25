import RestoreIcon from "@mui/icons-material/Restore";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardHeader,
  Grid,
  IconButton,
  Modal,
  Pagination,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { useHistory } from "react-router-dom";

import { useAsyncWithThrow } from "../../hooks/useAsyncWithThrow";
import { usePage } from "../../hooks/usePage";
import { formatDate } from "../../services/DateUtil";
import { Confirmable } from "../common/Confirmable";

import { EntryAttributes } from "./EntryAttributes";

import { Loading } from "components/common/Loading";
import { SearchBox } from "components/common/SearchBox";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";
import { EntryList as ConstEntryList } from "services/Constants";

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

const HeaderTableCell = styled(TableCell)(({ theme }) => ({
  color: theme.palette.primary.contrastText,
}));

interface Props {
  entityId: number;
  initialKeyword?: string | null;
}

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
  width: "50%",
}));

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "&:last-child td, &:last-child th": {
    border: 0,
  },
}));

const ItemNameTableCell = styled(TableCell)(() => ({
  width: "400px",
  wordBreak: "break-word",
}));

const ItemValueTableCell = styled(TableCell)(() => ({
  width: "750px",
  wordBreak: "break-word",
}));

export const RestorableEntryList: FC<Props> = ({
  entityId,
  initialKeyword,
}) => {
  const history = useHistory();

  const [page, changePage] = usePage();

  const [keyword, setKeyword] = useState(initialKeyword ?? "");
  const [openModal, setOpenModal] = useState(false);
  const [selectedEntryId, setSelectedEntryId] = useState<number>();

  const entries = useAsyncWithThrow(async () => {
    return await aironeApiClientV2.getEntries(entityId, false, page, keyword);
  }, [page, keyword]);

  const entryDetail = useAsyncWithThrow(async () => {
    if (selectedEntryId == null) {
      return null;
    }
    return await aironeApiClientV2.getEntry(selectedEntryId);
  }, [selectedEntryId]);

  const handleRestore = async (entryId: number) => {
    await aironeApiClientV2.restoreEntry(entryId);
    history.go(0);
  };

  const totalPageCount = entries.loading
    ? 0
    : Math.ceil((entries.value?.count ?? 0) / ConstEntryList.MAX_ROW_COUNT);

  return (
    <Box>
      {/* This box shows search box and create button */}
      <Box display="flex" justifyContent="space-between" mb="16px">
        <Box width={500}>
          <SearchBox
            placeholder="エントリを絞り込む"
            value={keyword}
            onChange={(e) => {
              setKeyword(e.target.value);
              /* Reset page number to prevent vanishing entities from display
               * when user move other page */
              changePage(1);
            }}
          />
        </Box>
      </Box>

      {/* This box shows each entry Cards */}
      {entries.loading ? (
        <Loading />
      ) : (
        <Grid container spacing={2}>
          {entries.value?.results?.map((entry) => {
            return (
              <Grid item xs={4} key={entry.id}>
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
      )}
      <Box display="flex" justifyContent="center" my="30px">
        <Stack spacing={2}>
          <Pagination
            count={totalPageCount}
            page={page}
            onChange={(_, newPage) => changePage(newPage)}
            color="primary"
          />
        </Stack>
      </Box>
      <StyledModal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        open={openModal}
        onClose={() => setOpenModal(false)}
      >
        <PaperBox>
          {!entryDetail.loading && entryDetail.value != null && (
            <>
              <Typography color="primary" my={2}>
                Operation Information
              </Typography>
              <TableContainer component={Paper}>
                <Table>
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
                        {entryDetail.value?.deletedUser?.username}
                      </ItemValueTableCell>
                    </StyledTableRow>
                    <StyledTableRow>
                      <ItemNameTableCell>Deleted at</ItemNameTableCell>
                      <ItemValueTableCell>
                        {entryDetail.value?.deletedTime != null
                          ? formatDate(entryDetail.value.deletedTime)
                          : null}
                      </ItemValueTableCell>
                    </StyledTableRow>
                  </TableBody>
                </Table>
              </TableContainer>
              <Typography color="primary" my={2}>
                Attributes & Values
              </Typography>
              {entryDetail.value?.attrs != null && (
                <EntryAttributes attributes={entryDetail.value.attrs} />
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
                  onClickYes={() => handleRestore(entryDetail.value?.id ?? 0)}
                />
                <Button
                  variant="outlined"
                  sx={{ margin: "0 4px" }}
                  onClick={() => setOpenModal(false)}
                >
                  キャンセル
                </Button>
              </Box>
            </>
          )}
        </PaperBox>
      </StyledModal>
    </Box>
  );
};
