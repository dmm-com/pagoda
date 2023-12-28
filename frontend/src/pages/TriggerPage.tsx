import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import {
  Box,
  Button,
  Container,
  Divider,
  IconButton,
  List,
  ListItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import React, { FC, useState } from "react";
import { Link, useHistory } from "react-router-dom";
import { useAsync } from "react-use";

import { topPath } from "Routes";
import { useSnackbar } from "notistack";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { ExtendButtonBaseTypeMap } from "@mui/material/ButtonBase/ButtonBase";
import { IconButtonTypeMap } from "@mui/material/IconButton/IconButton";
import { Loading } from "components/common/Loading";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { PageHeader } from "components/common/PageHeader";
import { usePage } from "hooks/usePage";
import { aironeApiClientV2 } from "repository/AironeApiClientV2";

import { Confirmable } from "components/common/Confirmable";
import { editTriggerPath, triggersPath, newTriggerPath } from "Routes";
import { TriggerAction, TriggerCondition } from "@dmm-com/airone-apiclient-typescript-fetch";

const StyledList = styled(List)(() => ({
  padding: "0",
}));

const StyledListItem = styled(ListItem)(() => ({
  padding: "4px",
}));

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  margin: theme.spacing(1),
})) as OverridableComponent<ExtendButtonBaseTypeMap<IconButtonTypeMap>>;

const HeaderTableRow = styled(TableRow)(({ }) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({ }) => ({
  color: "#FFFFFF",
}));

const StyledTableRow = styled(TableRow)(() => ({
  "&:nth-of-type(odd)": {
    backgroundColor: "#607D8B0A",
  },
  "& td": {
    padding: "8px 16px",
  },
}));

const StyledBox = styled(Box)(() => ({
  display: "flex",
  gap: "20px",
}));

const TriggerCondition: FC<{
  cond: TriggerCondition;
}> = ({ cond }) => {
  return (
    <StyledBox key={cond.id}>
      <Box>{cond.attr.name}</Box>
      <Divider orientation="vertical" flexItem />
      <Box>
        {cond.strCond}
      </Box>
    </StyledBox>
  );
};

const TriggerAction: FC<{
  action: TriggerAction;
}> = ({ action }) => {
  return (
    <StyledBox key={action.id}>
      <Box>{action.attr.name}</Box>
      <Divider orientation="vertical" flexItem />
      <Box>
        {action.values.map((value) => {
          return (
            <Box>
              {value.strCond}
            </Box>
          );
        })}
      </Box>
    </StyledBox>
  );
};

export const TriggerPage: FC = () => {
  const history = useHistory();
  const [page, changePage] = usePage();
  const [keyword, setKeyword] = useState("");
  const params = new URLSearchParams(location.search);
  const [query, setQuery] = useState<string>(params.get("query") ?? "");
  const [toggle, setToggle] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const triggers = useAsync(async () => {
    return await aironeApiClientV2.getTriggers(page);
  }, [page, query, toggle]);

  const handleDelete = async (triggerId: number) => {
    try {
      await aironeApiClientV2.deleteRole(triggerId);
      enqueueSnackbar(`トリガーの削除が完了しました`, {
        variant: "success",
      });
      history.replace(topPath());
      history.replace(triggersPath());
      setToggle(!toggle);
    } catch (e) {
      enqueueSnackbar("トリガーの削除が失敗しました", {
        variant: "error",
      });
    }
  };

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={Link} to={topPath()}>
          Top
        </Typography>
        <Typography color="textPrimary">トリガー管理</Typography>
      </AironeBreadcrumbs>
      <PageHeader title="トリガー管理">
        <Button
          variant="contained"
          color="secondary"
          component={Link}
          to={newTriggerPath()}
          sx={{ height: "48px", borderRadius: "24px", ml: "16px" }}
        >
          <AddIcon /> 新規トリガー/アクションを作成
        </Button>
      </PageHeader>
      <Container>
        <Box>
          {triggers.loading ? (
            <Loading />
          ) : (
            <>
              <Table>
                <TableHead>
                  <HeaderTableRow>
                    <HeaderTableCell width="200px">
                      エンティティ
                    </HeaderTableCell>
                    <HeaderTableCell width="420px">条件</HeaderTableCell>
                    <HeaderTableCell width="420px">アクション</HeaderTableCell>
                    <HeaderTableCell width="20px"></HeaderTableCell>
                    <HeaderTableCell width="20px"></HeaderTableCell>
                  </HeaderTableRow>
                </TableHead>
                <TableBody>
                  {triggers.value?.results?.map((trigger) => {
                    return (
                      <StyledTableRow key={trigger.id}>
                        <TableCell>{trigger.entity.name}</TableCell>
                        <TableCell>
                          <StyledList>
                            {trigger.conditions?.map((condition, n) => {
                              return (
                                <StyledListItem key={n}>
                                  <TriggerCondition cond={condition} />
                                </StyledListItem>
                              );
                            })}
                          </StyledList>
                        </TableCell>
                        <TableCell>
                          <StyledList>
                            {trigger.actions.map((action, n) => {
                              return (
                                <StyledListItem key={n}>
                                  <TriggerAction action={action} />
                                </StyledListItem>
                              );
                            })}
                          </StyledList>
                        </TableCell>

                        {/* Delete TriggerParent */}
                        <TableCell>
                          <Confirmable
                            componentGenerator={(handleOpen) => (
                              <StyledIconButton
                                onClick={handleOpen}
                              >
                                <DeleteOutlineIcon />
                              </StyledIconButton>
                            )}
                            dialogTitle="本当に削除しますか？"
                            onClickYes={() => handleDelete(trigger.id)}
                          />
                        </TableCell>

                        {/* Edit TriggerParent */}
                        <TableCell>
                          <StyledIconButton
                            component={Link}
                            to={editTriggerPath(trigger.id)}
                          >
                            <EditOutlinedIcon />
                          </StyledIconButton>
                        </TableCell>
                      </StyledTableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </>
          )}
        </Box>
      </Container >
    </Box >
  );
};
