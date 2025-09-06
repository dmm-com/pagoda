import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Avatar,
  Chip,
  LinearProgress,
  Alert,
  Divider,
  IconButton,
  Tooltip,
} from "@mui/material";
import Dashboard from "@mui/icons-material/Dashboard";
import Speed from "@mui/icons-material/Speed";
import Assessment from "@mui/icons-material/Assessment";
import Notifications from "@mui/icons-material/Notifications";
import Settings from "@mui/icons-material/Settings";
import Refresh from "@mui/icons-material/Refresh";
import Timeline from "@mui/icons-material/Timeline";
import People from "@mui/icons-material/People";
import Storage from "@mui/icons-material/Storage";

interface PluginAPI {
  ui?: {
    showNotification?: (message: string, type: string) => void;
  };
  routing?: {
    navigate?: (path: string) => void;
  };
}

interface EnhancedDashboardProps {
  pluginAPI?: PluginAPI; // Will be injected by the plugin system
}

const EnhancedDashboard: React.FC<EnhancedDashboardProps> = ({ pluginAPI }) => {
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [stats, setStats] = useState({
    activeEntities: 156,
    userActivity: 89,
    systemPerformance: 94,
    dataProcessed: 234,
  });

  const recentActivities = [
    {
      user: "admin",
      action: "Updated entity 'User'",
      time: "5 minutes ago",
      type: "update",
    },
    {
      user: "user1",
      action: "Created entry 'Test Data'",
      time: "12 minutes ago",
      type: "create",
    },
    {
      user: "user2",
      action: "Edited category 'Project'",
      time: "28 minutes ago",
      type: "edit",
    },
    {
      user: "admin",
      action: "Enabled plugin 'Dashboard'",
      time: "1 hour ago",
      type: "system",
    },
  ];

  const systemMetrics = [
    {
      title: "Active Entities",
      value: stats.activeEntities,
      icon: <Dashboard />,
      trend: "+12%",
      color: "primary",
    },
    {
      title: "User Activity",
      value: `${stats.userActivity}%`,
      icon: <People />,
      trend: "+5%",
      color: "success",
    },
    {
      title: "System Performance",
      value: `${stats.systemPerformance}%`,
      icon: <Speed />,
      trend: "+2%",
      color: "info",
    },
    {
      title: "Data Processed",
      value: `${stats.dataProcessed}MB`,
      icon: <Storage />,
      trend: "+18%",
      color: "warning",
    },
  ];

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setStats((prev) => ({
        activeEntities: prev.activeEntities + Math.floor(Math.random() * 3) - 1,
        userActivity: Math.min(
          100,
          Math.max(0, prev.userActivity + Math.floor(Math.random() * 6) - 3),
        ),
        systemPerformance: Math.min(
          100,
          Math.max(
            0,
            prev.systemPerformance + Math.floor(Math.random() * 4) - 2,
          ),
        ),
        dataProcessed: prev.dataProcessed + Math.floor(Math.random() * 10),
      }));
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setLastRefresh(new Date());

    if (pluginAPI?.ui?.showNotification) {
      pluginAPI.ui.showNotification("Dashboard refreshed", "info");
    }

    // Simulate API call
    setTimeout(() => {
      setStats((prev) => ({
        ...prev,
        userActivity: Math.min(
          100,
          prev.userActivity + Math.floor(Math.random() * 10),
        ),
      }));
    }, 1000);
  };

  const handleNavigateToSettings = () => {
    if (pluginAPI?.routing?.navigate) {
      pluginAPI.routing.navigate("/settings");
    } else {
      console.log("Navigate to settings requested");
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case "create":
        return "success";
      case "update":
        return "info";
      case "edit":
        return "warning";
      case "system":
        return "secondary";
      default:
        return "default";
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <Dashboard sx={{ fontSize: 32, color: "primary.main", mr: 2 }} />
          <Box>
            <Typography variant="h4" component="h1">
              Enhanced Dashboard
            </Typography>
            <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
              <Chip label="Plugin Enhanced" size="small" color="secondary" />
              <Chip label="Real-time Updates" size="small" color="success" />
              <Chip label="External Package" size="small" color="primary" />
            </Box>
          </Box>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Last Updated: {lastRefresh.toLocaleTimeString()}
          </Typography>
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} size="small">
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        This dashboard is provided by the{" "}
        <strong>@airone/plugin-dashboard</strong> package, overriding the
        existing dashboard route with enhanced features.
      </Alert>

      {/* System Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {systemMetrics.map((metric, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card elevation={1} sx={{ height: "100%" }}>
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                  <Box sx={{ color: `${metric.color}.main`, mr: 1 }}>
                    {metric.icon}
                  </Box>
                  <Typography
                    variant="caption"
                    sx={{ flexGrow: 1, fontSize: "0.75rem" }}
                  >
                    {metric.title}
                  </Typography>
                  <Chip label={metric.trend} size="small" color="success" />
                </Box>
                <Typography variant="h5" component="div" sx={{ mb: 1 }}>
                  {metric.value}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={
                    typeof metric.value === "string"
                      ? parseInt(metric.value.replace("%", ""))
                      : Math.min(100, (metric.value / 200) * 100)
                  }
                  color={
                    metric.color as
                      | "primary"
                      | "secondary"
                      | "success"
                      | "error"
                      | "info"
                      | "warning"
                  }
                  sx={{ height: 4, borderRadius: 2 }}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Activities */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                <Timeline sx={{ mr: 1, color: "primary.main" }} />
                <Typography variant="h6">Recent Activities</Typography>
              </Box>

              {recentActivities.map((activity, index) => (
                <Box key={index}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      py: 1.5,
                    }}
                  >
                    <Avatar
                      sx={{
                        bgcolor: "primary.light",
                        width: 32,
                        height: 32,
                        mr: 2,
                      }}
                    >
                      {activity.user[0].toUpperCase()}
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2">
                        <strong>{activity.user}</strong> {activity.action}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {activity.time}
                      </Typography>
                    </Box>
                    <Chip
                      label={activity.type}
                      size="small"
                      color={
                        getActivityColor(activity.type) as
                          | "default"
                          | "primary"
                          | "secondary"
                          | "success"
                          | "error"
                          | "info"
                          | "warning"
                      }
                      variant="outlined"
                    />
                  </Box>
                  {index < recentActivities.length - 1 && <Divider />}
                </Box>
              ))}
            </CardContent>
            <CardActions>
              <Button size="small" startIcon={<Assessment />}>
                View All
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<Notifications />}
                  fullWidth
                  onClick={() => {
                    if (pluginAPI?.ui?.showNotification) {
                      pluginAPI.ui.showNotification(
                        "Opening notification settings",
                        "info",
                      );
                    }
                  }}
                >
                  Notification Settings
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Settings />}
                  fullWidth
                  onClick={handleNavigateToSettings}
                >
                  System Settings
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Assessment />}
                  fullWidth
                  onClick={() => {
                    if (pluginAPI?.ui?.showNotification) {
                      pluginAPI.ui.showNotification(
                        "Report generation started",
                        "success",
                      );
                    }
                  }}
                >
                  Generate Report
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Plugin Status */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Plugin Status
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Typography variant="body2">Dashboard Plugin</Typography>
                  <Chip label="Active" size="small" color="success" />
                </Box>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Typography variant="body2">Route Override</Typography>
                  <Chip label="Enabled" size="small" color="primary" />
                </Box>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Typography variant="body2">Real-time Updates</Typography>
                  <Chip label="Running" size="small" color="info" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EnhancedDashboard;
