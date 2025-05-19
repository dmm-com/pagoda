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
import React, { FC, useState } from "react";

import { EntryAttributes } from "./EntryAttributes";

import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PaginationFooter } from "components/common/PaginationFooter";
import { SearchBox } from "components/common/SearchBox";
import { useAsyncWithThrow } from "hooks/useAsyncWithThrow";
import { usePage } from "hooks/usePage";
import { aironeApiClient } from "repository/AironeApiClient";
import { restoreEntryPath } from "routes/Routes";
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

interface Props {
  entityId: number;
}

export const RestorableEntryList: FC<Props> = ({ entityId }) => {
  const { enqueueSnackbar } = useSnackbar();

  const { page, query, changePage, changeQuery } = usePage();

  const [openModal, setOpenModal] = useState(false);
  const [selectedEntryId, setSelectedEntryId] = useState<number>();

  const entries = useAsyncWithThrow(async () => {
    return await aironeApiClient.getEntries(entityId, false, page, query);
  }, [page, query]);

  const entryDetail = useAsyncWithThrow(async () => {
    if (selectedEntryId == null) {
      return null;
    }
    return await aironeApiClient.getEntry(selectedEntryId);
  }, [selectedEntryId]);

  const handleChangeQuery = changeQuery;

  const handleRestore = async (entryId: number) => {
    await aironeApiClient
      .restoreEntry(entryId)
      .then(() => {
        enqueueSnackbar("アイテムの復旧が完了しました", {
          variant: "success",
        });
        window.location.href = restoreEntryPath(entityId, query);
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
      {entries.loading ? (
        <Loading />
      ) : (
        <Grid container spacing={2} id="entry_list">
          {entries.value?.results?.map((entry) => {
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
      )}
      <PaginationFooter
        count={entries.value?.count ?? 0}
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
          {entryDetail.loading ? (
            <Loading />
          ) : (
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
                        {entryDetail.value?.deletedUser?.username}
                      </ItemValueTableCell>
                    </StyledTableRow>
                    <StyledTableRow>
                      <ItemNameTableCell>Deleted at</ItemNameTableCell>
                      <ItemValueTableCell>
                        {entryDetail.value?.deletedTime != null
                          ? formatDateTime(entryDetail.value.deletedTime)
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
