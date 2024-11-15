import {
  EntryAttributeTypeTypeEnum,
  TriggerAction,
  TriggerActionValue,
  TriggerCondition,
} from "@dmm-com/airone-apiclient-typescript-fetch";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import {
  Box,
  Button,
  Checkbox,
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
import { ExtendButtonBaseTypeMap } from "@mui/material/ButtonBase/ButtonBase";
import { IconButtonTypeMap } from "@mui/material/IconButton/IconButton";
import { OverridableComponent } from "@mui/material/OverridableComponent";
import { styled } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import React, { FC, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAsync } from "react-use";

import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { aironeApiClient } from "repository/AironeApiClient";
import {
  editTriggerPath,
  entryDetailsPath,
  newTriggerPath,
  topPath,
  triggersPath,
} from "routes/Routes";

const StyledList = styled(List)(() => ({
  padding: "0",
}));

const StyledListItem = styled(ListItem)(() => ({
  padding: "4px",
}));

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  margin: theme.spacing(1),
})) as OverridableComponent<ExtendButtonBaseTypeMap<IconButtonTypeMap>>;

const HeaderTableRow = styled(TableRow)(({}) => ({
  backgroundColor: "#455A64",
}));

const HeaderTableCell = styled(TableCell)(({}) => ({
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

const ElemTriggerCondition: FC<{
  cond: TriggerCondition;
}> = ({ cond }) => {
  switch (cond.attr.type) {
    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return <Box>{cond.strCond}</Box>;

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return <Checkbox checked={cond.boolCond} disabled sx={{ p: "0px" }} />;

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <Box
          component={Link}
          to={entryDetailsPath(
            cond.refCond?.schema.id ?? 0,
            cond.refCond?.id ?? 0
          )}
        >
          {cond.refCond?.name ?? ""}
        </Box>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      return (
        <StyledBox>
          <Box>{cond.strCond}</Box>
          <Box
            component={Link}
            to={entryDetailsPath(
              cond.refCond?.schema.id ?? 0,
              cond.refCond?.id ?? 0
            )}
          >
            {cond.refCond?.name ?? ""}
          </Box>
        </StyledBox>
      );

    default:
      return <Box />;
  }
};

const TriggerCondition: FC<{
  cond: TriggerCondition;
}> = ({ cond }) => {
  return (
    <StyledBox key={cond.id}>
      <Box>{cond.attr.name}</Box>
      <Divider orientation="vertical" flexItem />
      <ElemTriggerCondition cond={cond} />
    </StyledBox>
  );
};

const ElemTriggerActionValue: FC<{
  action: TriggerAction;
  value: TriggerActionValue;
}> = ({ action, value }) => {
  switch (action.attr.type) {
    case EntryAttributeTypeTypeEnum.STRING:
    case EntryAttributeTypeTypeEnum.ARRAY_STRING:
      return <Box>{value.strCond}</Box>;

    case EntryAttributeTypeTypeEnum.BOOLEAN:
      return <Checkbox checked={value.boolCond} disabled sx={{ p: "0px" }} />;

    case EntryAttributeTypeTypeEnum.ARRAY_OBJECT:
    case EntryAttributeTypeTypeEnum.OBJECT:
      return (
        <Box
          component={Link}
          to={entryDetailsPath(
            value.refCond?.schema.id ?? 0,
            value.refCond?.id ?? 0
          )}
        >
          {value.refCond?.name ?? ""}
        </Box>
      );

    case EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT:
    case EntryAttributeTypeTypeEnum.NAMED_OBJECT:
      return (
        <StyledBox>
          <Box>{value.strCond}</Box>
          <Box
            component={Link}
            to={entryDetailsPath(
              value.refCond?.schema.id ?? 0,
              value.refCond?.id ?? 0
            )}
          >
            {value.refCond?.name ?? ""}
          </Box>
        </StyledBox>
      );

    default:
      return <Box />;
  }
};

const TriggerAction: FC<{
  action: TriggerAction;
}> = ({ action }) => {
  return (
    <StyledBox key={action.id}>
      <Box>{action.attr.name}</Box>
      <Divider orientation="vertical" flexItem />
      <StyledList>
        {action.values.map((value, index) => {
          return (
            <StyledListItem key={index}>
              <ElemTriggerActionValue action={action} value={value} />
            </StyledListItem>
          );
        })}
      </StyledList>
    </StyledBox>
  );
};

export const TriggerListPage: FC = () => {
  const navigate = useNavigate();
  const [toggle, setToggle] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const triggers = useAsync(async () => {
    return await aironeApiClient.getTriggers();
  }, [toggle]);

  const handleDelete = async (triggerId: number) => {
    try {
      await aironeApiClient.deleteTrigger(triggerId);
      enqueueSnackbar(`トリガーの削除が完了しました`, {
        variant: "success",
      });
      navigate(topPath(), { replace: true });
      navigate(triggersPath(), { replace: true });
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
          <AddIcon />
          新規トリガーを作成
        </Button>
      </PageHeader>
      <Container>
        <Box>
          {triggers.loading ? (
            <Loading />
          ) : (
            <>
              <Table data-testid="TriggerList">
                <TableHead>
                  <HeaderTableRow>
                    <HeaderTableCell width="200px">モデル</HeaderTableCell>
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
                              <StyledIconButton onClick={handleOpen}>
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
      </Container>
    </Box>
  );
};
