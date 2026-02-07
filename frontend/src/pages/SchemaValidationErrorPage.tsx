import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import {
  Box,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";
import { FC, useCallback } from "react";
import { z } from "zod";

import { topPath } from "../routes/Routes";

interface Props {
  /** The entity name that failed validation */
  entityName?: string;
  /** The plugin name that defined the schema */
  pluginName?: string;
  /** Zod validation errors */
  errors: z.ZodIssue[];
}

/**
 * Error page displayed when an entity fails plugin schema validation
 *
 * This page is shown when a plugin defines an entitySchema and the
 * target entity does not meet the requirements.
 */
export const SchemaValidationErrorPage: FC<Props> = ({
  entityName,
  pluginName,
  errors,
}) => {
  const handleClickGoToTop = useCallback(() => {
    location.href = topPath();
  }, []);

  return (
    <Box
      display="flex"
      flexDirection="column"
      flexGrow={1}
      alignItems="center"
      justifyContent="center"
      p={4}
    >
      <Box display="flex" my="32px" alignItems="center" gap={2}>
        <ErrorOutlineIcon sx={{ fontSize: 48, color: "#B0BEC5" }} />
        <Typography variant="h4" color="#B0BEC5" fontWeight="bold">
          Entity Schema Mismatch
        </Typography>
      </Box>

      <Box display="flex" flexDirection="column" alignItems="center" mb={3}>
        <Typography color="#455A64" paragraph>
          {entityName
            ? `The entity "${entityName}" does not meet the requirements defined by the plugin.`
            : "This entity does not meet the plugin's requirements."}
        </Typography>
        {pluginName && (
          <Typography color="#455A64" variant="body2">
            Plugin: {pluginName}
          </Typography>
        )}
      </Box>

      <Card sx={{ maxWidth: 600, width: "100%", mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Validation Errors
          </Typography>
          <List dense>
            {errors.map((error, index) => (
              <ListItem key={index} sx={{ py: 0.5 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <ErrorOutlineIcon color="error" fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={error.message}
                  secondary={
                    error.path.length > 0
                      ? `Path: ${error.path.join(".")}`
                      : undefined
                  }
                  primaryTypographyProps={{ variant: "body2" }}
                  secondaryTypographyProps={{ variant: "caption" }}
                />
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      <Box display="flex" flexDirection="column" alignItems="center">
        <Typography color="#455A64" variant="body2" paragraph>
          To use this plugin, ensure the entity has the required attributes with
          correct types.
        </Typography>
        <Button
          variant="contained"
          color="secondary"
          sx={{ borderRadius: "16px" }}
          onClick={handleClickGoToTop}
        >
          Back to Top
        </Button>
      </Box>
    </Box>
  );
};
