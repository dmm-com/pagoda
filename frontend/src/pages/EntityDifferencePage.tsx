import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Container,
  TextField,
  Typography,
} from "@mui/material";
import { DateTimePicker } from "@mui/x-date-pickers";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { FC, Suspense, useState } from "react";
import { preload } from "swr";

import { Loading } from "components/common/Loading";
import { PageHeader } from "components/common/PageHeader";
import { EntityBreadcrumbs } from "components/entity/EntityBreadcrumbs";
import { useIdParams } from "hooks/useIdParams";
import { usePagodaSWR, wrapFetcher } from "hooks/usePagodaSWR";
import { useTranslation } from "hooks/useTranslation";
import { aironeApiClient } from "repository/AironeApiClient";

const EntityDifferenceContent: FC<{ entityId: number }> = ({ entityId }) => {
  const { t } = useTranslation();
  const [attrs, setAttrs] = useState<{ id: number; name: string }[]>([]);
  const [startDateTime, setStartDateTime] = useState<Date | null>(null);
  const [endDateTime, setEndDateTime] = useState<Date | null>(() => new Date());
  const [showRangeError, setShowRangeError] = useState(false);

  const { data: entity } = usePagodaSWR(
    ["entity", entityId],
    () => aironeApiClient.getEntity(entityId),
    { suspense: true },
  );

  return (
    <>
      <EntityBreadcrumbs entity={entity} title={t("entity.difference.show")} />

      <PageHeader
        title={entity.name}
        description={t("entity.difference.show")}
      />

      <Container>
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
            <Autocomplete
              multiple
              sx={{ width: 300 }}
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
            />
            <Typography>-</Typography>
            <DateTimePicker
              label={t("entity.difference.endDateTime")}
              format="yyyy/MM/dd HH:mm:ss"
              value={endDateTime}
              onChange={setEndDateTime}
              slotProps={{ textField: { size: "small" } }}
            />
            <Button
              variant="contained"
              color="secondary"
              onClick={() => {
                setShowRangeError(
                  startDateTime != null &&
                    endDateTime != null &&
                    endDateTime.getTime() <= startDateTime.getTime(),
                );
              }}
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
