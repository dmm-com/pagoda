import React from "react";
import { Box, Typography, Card, CardContent, Chip } from "@mui/material";
import { useParams } from "react-router";

/**
 * Sample Entry List Page - Minimal implementation for Phase 1
 * Displays "Plugin View Active" message with entityId from URL
 */
const SampleEntryListPage: React.FC = () => {
  const { entityId } = useParams<{ entityId: string }>();

  return (
    <Box sx={{ p: 4, maxWidth: 900, mx: "auto" }}>
      <Card elevation={2}>
        <CardContent>
          <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
            <Typography variant="h4" component="h1">
              Plugin View Active
            </Typography>
            <Chip
              label="Sample Plugin"
              size="small"
              color="primary"
              sx={{ ml: 2 }}
            />
          </Box>

          <Typography variant="body1" paragraph>
            This page is rendered by the <strong>plugin-entity-sample</strong>{" "}
            plugin instead of the default EntryListPage.
          </Typography>

          <Box
            sx={{
              mt: 3,
              p: 2,
              backgroundColor: "grey.100",
              borderRadius: 1,
            }}
          >
            <Typography variant="subtitle2" gutterBottom>
              Route Information:
            </Typography>
            <Typography
              variant="body2"
              component="pre"
              sx={{ fontFamily: "monospace", fontSize: "0.9rem" }}
            >
              {`Entity ID: ${entityId ?? "N/A"}
Page Type: entry.list
Plugin ID: sample`}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SampleEntryListPage;
