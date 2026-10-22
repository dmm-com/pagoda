import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Container,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { FC, Fragment, ReactNode, Suspense, useState } from "react";
import { Link } from "react-router";
import { preload } from "swr";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { useIdParams } from "hooks/useIdParams";
import { usePagodaSWR, wrapFetcher } from "hooks/usePagodaSWR";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient, EntityDiff } from "repository/AironeApiClient";
import { entryDetailsPath } from "routes/Routes";

const HEADER_GRAY_COLOR = "#F9FAFA";
const START_HEADER_COLOR = "#FFF3F3";
const END_HEADER_COLOR = "#F0FFF0";
const START_VALUE_COLOR = "#FFF6F6";
const END_VALUE_COLOR = "#F6FFF6";
const EMPTY_VALUE_COLOR = "#F6F6F6";
const WHITE = "#FFFFFF";

// The table fills the available width and the value columns share the space
// equally. Once a value column would get narrower than MIN_VALUE_WIDTH (px),
// the table keeps that width and scrolls horizontally instead.
const ITEM_NAME_WIDTH = 200;
const MIN_VALUE_WIDTH = 150;
// a value column whose rows are all empty is shrunk to this width (px)
const EMPTY_COLUMN_WIDTH = 50;

const isObjectValue = (
  value: unknown,
): value is { id: number | string; name?: string } =>
  typeof value === "object" &&
  value !== null &&
  "id" in value &&
  (typeof value.id === "number" || typeof value.id === "string");

// NAMED_* values are serialized as {"<name>": <object | null>}; an unset one is {"": null}
const isEmptyNamedValue = (value: unknown): boolean => {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }
  const keys = Object.keys(value);
  return (
    keys.length === 1 &&
    keys[0] === "" &&
    (value as Record<string, unknown>)[""] == null
  );
};

// null, "", [] and {"": null} are all treated as an empty value
const isEmptyValue = (value: unknown): boolean =>
  value == null ||
  value === "" ||
  (Array.isArray(value) && value.length === 0) ||
  isEmptyNamedValue(value);

const formatValue = (value: unknown): string =>
  value == null
    ? ""
    : typeof value === "string"
      ? value
      : JSON.stringify(value);

const renderScalar = (value: unknown, type: number | undefined): ReactNode => {
  if (isObjectValue(value)) {
    if (type === EntryAttributeTypeTypeEnum.OBJECT) {
      // the value is an entry, so link to it (the entity id is not needed to resolve it)
      return (
        <Link to={entryDetailsPath(0, value.id)}>
          {value.name ?? String(value.id)}
        </Link>
      );
    }
    return value.name ?? String(value.id);
  }
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    // named value: {"<name>": <object | scalar>}
    return Object.entries(value).map(([key, v], i) => (
      <Fragment key={key}>
        {i > 0 && ", "}
        {key}: {renderScalar(v, EntryAttributeTypeTypeEnum.OBJECT)}
      </Fragment>
    ));
  }
  return formatValue(value);
};

const ARRAY_TYPES: number[] = [
  EntryAttributeTypeTypeEnum.ARRAY_STRING,
  EntryAttributeTypeTypeEnum.ARRAY_OBJECT,
  EntryAttributeTypeTypeEnum.ARRAY_NAMED_OBJECT,
  EntryAttributeTypeTypeEnum.ARRAY_GROUP,
  EntryAttributeTypeTypeEnum.ARRAY_ROLE,
];

const renderValue = (value: unknown, type: number | undefined): ReactNode => {
  if (isEmptyValue(value)) {
    return "";
  }
  if (
    type !== undefined &&
    ARRAY_TYPES.includes(type) &&
    Array.isArray(value)
  ) {
    const itemType =
      type === EntryAttributeTypeTypeEnum.ARRAY_OBJECT
        ? EntryAttributeTypeTypeEnum.OBJECT
        : undefined;
    return (
      <ul style={{ margin: 0, paddingLeft: "1.2em" }}>
        {value.map((v, i) => (
          <li key={i}>{renderScalar(v, itemType)}</li>
        ))}
      </ul>
    );
  }
  return renderScalar(value, type);
};

const EntityDifferenceContent: FC<{ entityId: number }> = ({ entityId }) => {
  const { t } = useTranslation();
  const [attrs, setAttrs] = useState<{ id: number; name: string }[]>([]);
  const [startDateTime, setStartDateTime] = useState<Date | null>(null);
  const [endDateTime, setEndDateTime] = useState<Date | null>(() => new Date());
  const [showRangeError, setShowRangeError] = useState(false);
  const [diff, setDiff] = useState<EntityDiff | null>(null);
  // attribute names used for the displayed result (the form may change afterwards)
  const [diffAttrNames, setDiffAttrNames] = useState<string[]>([]);
  const [fetchError, setFetchError] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleShow = async () => {
    const invalidRange =
      startDateTime != null &&
      endDateTime != null &&
      endDateTime.getTime() <= startDateTime.getTime();
    setShowRangeError(invalidRange);
    if (
      invalidRange ||
      attrs.length === 0 ||
      startDateTime == null ||
      endDateTime == null
    ) {
      return;
    }

    setLoading(true);
    setFetchError(false);
    // drop the previous result while the new one is being fetched
    setDiff(null);
    try {
      const attrNames = attrs.map((a) => a.name);
      setDiff(
        await aironeApiClient.getEntityDiff(
          entity.name,
          attrNames,
          startDateTime,
          endDateTime,
        ),
      );
      setDiffAttrNames(attrNames);
    } catch {
      setDiff(null);
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  };

  const { data: entity } = usePagodaSWR(
    ["entity", entityId],
    () => aironeApiClient.getEntity(entityId),
    { suspense: true },
  );

  // whether every row of each value column (start/end of each attribute) is empty
  const isEmptyColumn = (
    name: string,
    side: "value_t0" | "value_t1",
  ): boolean =>
    (diff?.items ?? []).every((item) =>
      isEmptyValue(item.attrs.find((x) => x.name === name)?.[side]),
    );
  const columnWidths = diffAttrNames.flatMap((name) =>
    (["value_t0", "value_t1"] as const).map((side) =>
      isEmptyColumn(name, side) ? EMPTY_COLUMN_WIDTH : undefined,
    ),
  );
  const minTableWidth =
    ITEM_NAME_WIDTH +
    columnWidths.reduce<number>((sum, w) => sum + (w ?? MIN_VALUE_WIDTH), 0);

  return (
    <>
      <EntityBreadcrumbs entity={entity} title={t("entity.difference.title")} />

      <PageHeader
        title={entity.name}
        description={t("entity.difference.desc")}
      />

      <Container>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
            <Autocomplete
              multiple
              disabled={loading}
              sx={{ flexGrow: 1, minWidth: 300 }}
              size="small"
              options={entity.attrs.map((a) => ({ id: a.id, name: a.name }))}
              getOptionLabel={(o) => o.name}
              isOptionEqualToValue={(o, v) => o.id === v.id}
              value={attrs}
              onChange={(_, value) => setAttrs(value)}
              renderInput={(params) => (
                <TextField {...params} label={t("entity.difference.attr")} />
              )}
            />
            <DateTimePicker
              label={t("entity.difference.startDateTime")}
              format="yyyy/MM/dd HH:mm:ss"
              value={startDateTime}
              onChange={setStartDateTime}
              slotProps={{ textField: { size: "small" } }}
              disabled={loading}
            />
            <Typography>-</Typography>
            <DateTimePicker
              label={t("entity.difference.endDateTime")}
              format="yyyy/MM/dd HH:mm:ss"
              value={endDateTime}
              onChange={setEndDateTime}
              slotProps={{ textField: { size: "small" } }}
              disabled={loading}
            />
            <Button
              variant="contained"
              color="secondary"
              onClick={handleShow}
              disabled={loading}
              sx={{ ml: "auto" }}
            >
              {t("entity.difference.show")}
            </Button>
          </Box>
        </LocalizationProvider>
        {showRangeError && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            {t("entity.difference.endBeforeStartError")}
          </Alert>
        )}
        {fetchError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {t("entity.difference.fetchError")}
          </Alert>
        )}
        {diff != null &&
          (diff.count === 0 ? (
            <Typography sx={{ mt: 2 }}>
              {t("entity.difference.noDifference")}
            </Typography>
          ) : (
            <Box sx={{ mt: 2 }}>
              <Typography sx={{ mb: 1 }}>
                {t("entity.difference.count", { count: diff.count })}
              </Typography>
              <TableContainer component={Paper}>
                <Table
                  size="small"
                  sx={{
                    tableLayout: "fixed",
                    width: "100%",
                    minWidth: minTableWidth,
                    "& td, & th": {
                      overflowWrap: "anywhere",
                      whiteSpace: "pre-wrap",
                    },
                  }}
                >
                  <colgroup>
                    <col style={{ width: ITEM_NAME_WIDTH }} />
                    {diffAttrNames.flatMap((name, i) => [
                      <col
                        key={`${name}-0`}
                        style={{ width: columnWidths[i * 2] }}
                      />,
                      <col
                        key={`${name}-1`}
                        style={{ width: columnWidths[i * 2 + 1] }}
                      />,
                    ])}
                  </colgroup>
                  <TableHead
                    sx={{ "& .MuiTableCell-head": { fontWeight: "bold" } }}
                  >
                    <TableRow>
                      <TableCell
                        rowSpan={2}
                        sx={{ bgcolor: HEADER_GRAY_COLOR }}
                      >
                        {t("entity.difference.entry")}
                      </TableCell>
                      {diffAttrNames.map((name, i) => (
                        <TableCell
                          key={name}
                          colSpan={2}
                          align="center"
                          // even-numbered (2nd, 4th, ...) attributes are shaded
                          sx={{
                            bgcolor: i % 2 === 1 ? HEADER_GRAY_COLOR : WHITE,
                          }}
                        >
                          {name}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      {diffAttrNames.map((name) => (
                        <Fragment key={name}>
                          <TableCell sx={{ bgcolor: START_HEADER_COLOR }}>
                            {t("entity.difference.startValue")}
                          </TableCell>
                          <TableCell sx={{ bgcolor: END_HEADER_COLOR }}>
                            {t("entity.difference.endValue")}
                          </TableCell>
                        </Fragment>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {diff.items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell sx={{ bgcolor: WHITE }}>
                          <Link to={entryDetailsPath(entityId, item.id)}>
                            {item.name}
                          </Link>
                        </TableCell>
                        {diffAttrNames.map((name) => {
                          const a = item.attrs.find((x) => x.name === name);
                          return (
                            <Fragment key={name}>
                              <TableCell
                                sx={{
                                  bgcolor: isEmptyValue(a?.value_t0)
                                    ? EMPTY_VALUE_COLOR
                                    : START_VALUE_COLOR,
                                }}
                              >
                                {renderValue(a?.value_t0, a?.type)}
                              </TableCell>
                              <TableCell
                                sx={{
                                  bgcolor: isEmptyValue(a?.value_t1)
                                    ? EMPTY_VALUE_COLOR
                                    : END_VALUE_COLOR,
                                }}
                              >
                                {renderValue(a?.value_t1, a?.type)}
                              </TableCell>
                            </Fragment>
                          );
                        })}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          ))}
      </Container>
    </>
  );
};

export const EntityDifferencePage: FC = () => {
  const { entityId } = useIdParams({ required: ["entityId"] });

  preload(
    ["entity", entityId],
    wrapFetcher(() => aironeApiClient.getEntity(entityId)),
  );

  return (
    <Box className="container">
      <Suspense fallback={<Loading />}>
        <EntityDifferenceContent entityId={entityId} />
      </Suspense>
    </Box>
  );
};
