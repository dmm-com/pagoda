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
import {
  Dashboard,
  Speed,
  Assessment,
  Notifications,
  Settings,
  Refresh,
  Timeline,
  People,
  Storage,
} from "@mui/icons-material";

interface EnhancedDashboardProps {
  pluginAPI?: any; // Will be injected by the plugin system
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
      action: "エンティティ「ユーザー」を更新",
      time: "5分前",
      type: "update",
    },
    {
      user: "user1",
      action: "エントリー「テストデータ」を作成",
      time: "12分前",
      type: "create",
    },
    {
      user: "user2",
      action: "カテゴリ「プロジェクト」を編集",
      time: "28分前",
      type: "edit",
    },
    {
      user: "admin",
      action: "プラグイン「Dashboard」を有効化",
      time: "1時間前",
      type: "system",
    },
  ];

  const systemMetrics = [
    {
      title: "アクティブエンティティ",
      value: stats.activeEntities,
      icon: <Dashboard />,
      trend: "+12%",
      color: "primary",
    },
    {
      title: "ユーザーアクティビティ",
      value: `${stats.userActivity}%`,
      icon: <People />,
      trend: "+5%",
      color: "success",
    },
    {
      title: "システムパフォーマンス",
      value: `${stats.systemPerformance}%`,
      icon: <Speed />,
      trend: "+2%",
      color: "info",
    },
    {
      title: "データ処理",
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
      pluginAPI.ui.showNotification("ダッシュボードを更新しました", "info");
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
              拡張ダッシュボード
            </Typography>
            <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
              <Chip label="Plugin Enhanced" size="small" color="secondary" />
              <Chip label="リアルタイム更新" size="small" color="success" />
              <Chip label="外部パッケージ" size="small" color="primary" />
            </Box>
          </Box>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            最終更新: {lastRefresh.toLocaleTimeString()}
          </Typography>
          <Tooltip title="更新">
            <IconButton onClick={handleRefresh} size="small">
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        このダッシュボードは <strong>@airone/plugin-dashboard</strong>{" "}
        パッケージによって
        既存のダッシュボードルートをオーバーライドして拡張機能を提供しています。
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
                  color={metric.color as any}
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
                <Typography variant="h6">最近のアクティビティ</Typography>
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
                        <strong>{activity.user}</strong> が {activity.action}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {activity.time}
                      </Typography>
                    </Box>
                    <Chip
                      label={activity.type}
                      size="small"
                      color={getActivityColor(activity.type) as any}
                      variant="outlined"
                    />
                  </Box>
                  {index < recentActivities.length - 1 && <Divider />}
                </Box>
              ))}
            </CardContent>
            <CardActions>
              <Button size="small" startIcon={<Assessment />}>
                すべて表示
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                クイックアクション
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<Notifications />}
                  fullWidth
                  onClick={() => {
                    if (pluginAPI?.ui?.showNotification) {
                      pluginAPI.ui.showNotification(
                        "通知設定を開きます",
                        "info",
                      );
                    }
                  }}
                >
                  通知設定
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Settings />}
                  fullWidth
                  onClick={handleNavigateToSettings}
                >
                  システム設定
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Assessment />}
                  fullWidth
                  onClick={() => {
                    if (pluginAPI?.ui?.showNotification) {
                      pluginAPI.ui.showNotification(
                        "レポート生成を開始しました",
                        "success",
                      );
                    }
                  }}
                >
                  レポート生成
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Plugin Status */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                プラグイン状態
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
                  <Chip label="アクティブ" size="small" color="success" />
                </Box>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Typography variant="body2">ルートオーバーライド</Typography>
                  <Chip label="有効" size="small" color="primary" />
                </Box>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Typography variant="body2">リアルタイム更新</Typography>
                  <Chip label="動作中" size="small" color="info" />
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
