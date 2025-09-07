import React from "react";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Alert,
  Divider,
} from "@mui/material";
import EmojiEmotions from "@mui/icons-material/EmojiEmotions";
import Celebration from "@mui/icons-material/Celebration";
import Settings from "@mui/icons-material/Settings";
import Info from "@mui/icons-material/Info";

interface PluginAPI {
  ui?: {
    showNotification?: (message: string, type: string) => void;
  };
  routing?: {
    navigate?: (path: string) => void;
  };
}

interface HelloWorldPageProps {
  pluginAPI?: PluginAPI; // Will be injected by the plugin system
}

const HelloWorldPage: React.FC<HelloWorldPageProps> = ({ pluginAPI }) => {
  const [clickCount, setClickCount] = React.useState(0);

  const handleSampleAction = () => {
    setClickCount((prev) => prev + 1);

    // Use plugin API if available
    if (pluginAPI?.ui?.showNotification) {
      pluginAPI.ui.showNotification(
        `Hello World plugin button clicked ${clickCount + 1} times!`,
        "success",
      );
    }
  };

  const handleNavigateExample = () => {
    if (pluginAPI?.routing?.navigate) {
      pluginAPI.routing.navigate("/");
    } else {
      window.location.href = "/";
    }
  };

  const handleShowMessage = () => {
    alert("Message from plugin: Hello World! 🎉");
  };

  return (
    <Box sx={{ p: 4, maxWidth: 900, mx: "auto" }}>
      <Card elevation={2}>
        <CardContent>
          {/* Header */}
          <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
            <EmojiEmotions
              sx={{ fontSize: 48, color: "primary.main", mr: 2 }}
            />
            <Box>
              <Typography variant="h4" component="h1">
                Hello World Plugin
              </Typography>
              <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
                <Chip label="v1.0.0" size="small" color="primary" />
                <Chip label="Sample Plugin" size="small" color="secondary" />
                <Chip label="External Package" size="small" color="success" />
              </Box>
            </Box>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              This is an external npm module compatible plugin implemented as
              the <strong>@airone/plugin-hello-world</strong> package.
            </Typography>
          </Alert>

          {/* Description */}
          <Typography variant="body1" paragraph>
            This plugin is a sample implementation of the Airone plugin system.
            It can be distributed as an external npm package and provides the
            following features:
          </Typography>

          <Box component="ul" sx={{ mb: 3, pl: 3 }}>
            <li>Distribution as an independent npm package</li>
            <li>Adding custom routes (/hello-world)</li>
            <li>Notification functionality using the plugin API</li>
            <li>Integration with Material-UI theme</li>
            <li>Error handling and fallback</li>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Interactive Demo */}
          <Typography variant="h6" gutterBottom>
            Interactive Demo
          </Typography>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <Button
                variant="contained"
                fullWidth
                startIcon={<Celebration />}
                onClick={handleSampleAction}
              >
                Notification Test ({clickCount})
              </Button>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Info />}
                onClick={handleShowMessage}
              >
                Show Message
              </Button>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Settings />}
                onClick={handleNavigateExample}
              >
                Go to Home
              </Button>
            </Grid>
          </Grid>

          {/* Plugin Information */}
          <Box
            sx={{ mt: 4, p: 2, backgroundColor: "grey.100", borderRadius: 1 }}
          >
            <Typography variant="subtitle2" gutterBottom>
              Plugin Information:
            </Typography>
            <Typography
              variant="body2"
              component="pre"
              sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}
            >
              {`Package Name: @airone/plugin-hello-world
ID: hello-world-plugin
Name: Hello World Plugin
Version: 1.0.0
Description: Sample plugin for demonstration
Distribution: External npm package
Dependencies: @airone/core ^1.0.0`}
            </Typography>
          </Box>

          {/* API Status */}
          <Box
            sx={{
              mt: 2,
              p: 2,
              backgroundColor: pluginAPI ? "success.light" : "warning.light",
              borderRadius: 1,
            }}
          >
            <Typography variant="subtitle2" gutterBottom>
              Plugin API Status:
            </Typography>
            <Typography variant="body2">
              {pluginAPI
                ? "✅ Plugin API is available - Notification and navigation features can be used"
                : "⚠️ Plugin API is not available - Only basic features will work"}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default HelloWorldPage;
