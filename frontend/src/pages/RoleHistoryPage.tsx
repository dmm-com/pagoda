import RestoreIcon from "@mui/icons-material/Restore";
import {
  Box,
  Button,
  Container,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { FC, useState } from "react";
import { Link, useNavigate } from "react-router";

import { AironeLink } from "components";
import { AironeBreadcrumbs } from "components/common/AironeBreadcrumbs";
import { Confirmable } from "components/common/Confirmable";
import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { PaginationFooter } from "components/common/PaginationFooter";
import { useIdParams } from "hooks/useIdParams";
import { usePage } from "hooks/usePage";
import { usePageTitle } from "hooks/usePageTitle";
import { usePagodaSWR } from "hooks/usePagodaSWR";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";
import { rolePath, rolesPath, topPath } from "routes/Routes";
import { ServerContext } from "services";
import { ACLType, ACLTypeLabels } from "services/ACLUtil";
import { formatDateTime } from "services/DateUtil";

export const RoleHistoryPage: FC = () => {
  const { roleId } = useIdParams({ required: ["roleId"] });
  const { page, changePage } = usePage();
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  usePageTitle(t("role.history.title"));
  const { data: histories } = usePagodaSWR(
    ["roleHistories", roleId, page],
    () => aironeApiClient.getRoleHistories(roleId, page),
  );
  const readonly = ServerContext.getInstance()?.user?.isReadonly ?? false;

  const restore = async (
    historyId: number,
    historySource: "role" | "permission",
  ) => {
    setSubmitting(true);
    try {
      await aironeApiClient.restoreRoleHistory(
        roleId,
        historyId,
        historySource,
      );
      enqueueSnackbar(t("role.history.accepted"), { variant: "success" });
      navigate(rolesPath());
    } catch {
      enqueueSnackbar(t("role.history.failed"), { variant: "error" });
    } finally {
      setSubmitting(false);
    }
  };

  if (!histories) return <Loading />;
  const role = histories.role;
  const fields: Array<[string, string]> = [
    ["users", t("role.form.userRegisterTitle")],
    ["groups", t("role.form.groupRegisterTitle")],
    [
      "admin_users",
      `${t("role.form.admin")} (${t("role.form.userRegisterTitle")})`,
    ],
    [
      "admin_groups",
      `${t("role.form.admin")} (${t("role.form.groupRegisterTitle")})`,
    ],
    ["permissions", t("role.history.permissions")],
  ];

  return (
    <Box className="container-fluid">
      <AironeBreadcrumbs>
        <Typography component={AironeLink} to={topPath()}>
          Top
        </Typography>
        <Typography component={AironeLink} to={rolesPath()}>
          {t("role.listPage.pageTitle")}
        </Typography>
        <Typography component={AironeLink} to={rolePath(roleId)}>
          {role.name}
        </Typography>
        <Typography>{t("role.history.title")}</Typography>
      </AironeBreadcrumbs>
      <PageHeader title={role.name} description={t("role.history.title")}>
        <Button
          component={Link}
          to={rolePath(roleId)}
          disabled={!role.is_active}
        >
          {t("common.edit")}
        </Button>
      </PageHeader>
      <Container>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t("entry.history.executedAtHeader")}</TableCell>
              <TableCell>{t("entry.history.executedByHeader")}</TableCell>
              <TableCell>{t("entry.selfHistory.operationHeader")}</TableCell>
              <TableCell>{t("role.history.state")}</TableCell>
              <TableCell>{t("common.restore")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {histories.results.map((history, index) => (
              <TableRow key={`${history.history_source}-${history.history_id}`}>
                <TableCell>
                  {formatDateTime(new Date(history.history_date))}
                </TableCell>
                <TableCell>
                  {history.history_user ?? "-"}
                  <Typography variant="caption">
                    {history.history_change_reason}
                  </Typography>
                </TableCell>
                <TableCell>
                  {!history.is_active
                    ? t("common.delete")
                    : history.history_type === "+"
                      ? t("common.create")
                      : t("common.update")}
                </TableCell>
                <TableCell>
                  <Typography>
                    {t("role.form.name")}: {history.name}
                  </Typography>
                  <Typography>
                    {t("role.form.description")}: {history.description}
                  </Typography>
                  {fields.map(([key, label]) => (
                    <Typography
                      key={key}
                      sx={
                        key === "permissions"
                          ? { whiteSpace: "pre-line" }
                          : undefined
                      }
                    >
                      {label}:{key === "permissions" ? "\n" : " "}
                      {history.relations[key]
                        ?.map((value) => {
                          if (key === "permissions") {
                            const level = Number(
                              value.codename?.split(".").at(-1),
                            ) as ACLType;
                            const name =
                              value.name ?? t("role.history.missingTarget");
                            return `${name}：${ACLTypeLabels[level] ?? t("common.unknown")}`;
                          }
                          return (
                            value.username ?? value.name ?? String(value.id)
                          );
                        })
                        .join(key === "permissions" ? "\n" : ", ") || "-"}
                    </Typography>
                  ))}
                </TableCell>
                <TableCell>
                  <Confirmable
                    componentGenerator={(open) => (
                      <IconButton
                        aria-label={t("common.restore")}
                        onClick={open}
                        disabled={
                          readonly ||
                          !role.is_editable ||
                          submitting ||
                          !history.is_active ||
                          (page === 1 && index === 0)
                        }
                      >
                        <RestoreIcon />
                      </IconButton>
                    )}
                    dialogTitle={t("role.history.confirm")}
                    onClickYes={() =>
                      restore(history.history_id, history.history_source)
                    }
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <PaginationFooter
          count={histories.count}
          maxRowCount={10}
          page={page}
          changePage={changePage}
        />
      </Container>
    </Box>
  );
};
