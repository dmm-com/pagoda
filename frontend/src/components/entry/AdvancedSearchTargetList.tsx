import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Link,
  Pagination,
  Typography,
} from "@mui/material";
import { FC } from "react";

import { useTranslation } from "hooks/useTranslation";
import { entryDetailsPath } from "routes/Routes";

export type AdvancedSearchTarget = {
  id: number;
  name: string;
  referrals?: Array<{
    id: number;
    name: string;
    schema: { id: number; name: string };
  }>;
};

interface Props {
  targets: AdvancedSearchTarget[];
  totalCount: number;
  page: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
  checkingReferences?: boolean;
}

export const AdvancedSearchTargetList: FC<Props> = ({
  targets,
  totalCount,
  page,
  onPageChange,
  pageSize = 10,
  checkingReferences = false,
}) => {
  const { t } = useTranslation();

  return (
    <Box>
      {targets.map((target) => (
        <Box key={target.id} sx={{ mb: 1 }}>
          <Typography fontWeight={600}>{target.name}</Typography>
          {(target.referrals?.length ?? 0) > 0 ? (
            <Accordion disableGutters>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                {t("advancedSearch.targetList.referenceCount", {
                  count: target.referrals?.length ?? 0,
                })}
              </AccordionSummary>
              <AccordionDetails>
                {target.referrals?.map((referral) => (
                  <Typography key={referral.id}>
                    <Link
                      href={entryDetailsPath(referral.schema.id, referral.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {referral.schema.name} / {referral.name}
                    </Link>
                  </Typography>
                ))}
              </AccordionDetails>
            </Accordion>
          ) : (
            !checkingReferences && (
              <Typography variant="body2" color="text.secondary">
                {t("advancedSearch.targetList.noReferences")}
              </Typography>
            )
          )}
        </Box>
      ))}
      {totalCount > pageSize && (
        <Pagination
          count={Math.ceil(totalCount / pageSize)}
          page={page}
          onChange={(_, nextPage) => onPageChange(nextPage)}
          sx={{ mt: 2, display: "flex", justifyContent: "center" }}
        />
      )}
    </Box>
  );
};
