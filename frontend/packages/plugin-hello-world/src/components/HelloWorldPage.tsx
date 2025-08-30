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
import {
  EmojiEmotions,
  Celebration,
  Settings,
  Info,
} from "@mui/icons-material";

interface HelloWorldPageProps {
  pluginAPI?: any; // Will be injected by the plugin system
}

const HelloWorldPage: React.FC<HelloWorldPageProps> = ({ pluginAPI }) => {
  const [clickCount, setClickCount] = React.useState(0);

  const handleSampleAction = () => {
    setClickCount((prev) => prev + 1);

    // Use plugin API if available
    if (pluginAPI?.ui?.showNotification) {
      pluginAPI.ui.showNotification(
        `Hello World プラグインのボタンが ${clickCount + 1} 回クリックされました！`,
        "success",
      );
    } else {
      console.log("Hello World Plugin: Button clicked!", clickCount + 1);
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
    alert("プラグインからのメッセージ：Hello World! 🎉");
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
                <Chip
                  label="サンプルプラグイン"
                  size="small"
                  color="secondary"
                />
                <Chip label="外部パッケージ" size="small" color="success" />
              </Box>
            </Box>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              これは <strong>@airone/plugin-hello-world</strong>{" "}
              パッケージとして実装された 外部npmモジュール対応プラグインです。
            </Typography>
          </Alert>

          {/* Description */}
          <Typography variant="body1" paragraph>
            このプラグインはAironeプラグインシステムのサンプル実装です。
            外部npmパッケージとして配布可能で、以下の機能を提供します：
          </Typography>

          <Box component="ul" sx={{ mb: 3, pl: 3 }}>
            <li>独立したnpmパッケージとしての配布</li>
            <li>カスタムルートの追加（/hello-world）</li>
            <li>プラグインAPIを使用した通知機能</li>
            <li>Material-UIテーマとの統合</li>
            <li>エラーハンドリングとフォールバック</li>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Interactive Demo */}
          <Typography variant="h6" gutterBottom>
            インタラクティブデモ
          </Typography>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <Button
                variant="contained"
                fullWidth
                startIcon={<Celebration />}
                onClick={handleSampleAction}
              >
                通知テスト ({clickCount})
              </Button>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Info />}
                onClick={handleShowMessage}
              >
                メッセージ表示
              </Button>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Settings />}
                onClick={handleNavigateExample}
              >
                ホームに移動
              </Button>
            </Grid>
          </Grid>

          {/* Plugin Information */}
          <Box
            sx={{ mt: 4, p: 2, backgroundColor: "grey.100", borderRadius: 1 }}
          >
            <Typography variant="subtitle2" gutterBottom>
              プラグイン情報:
            </Typography>
            <Typography
              variant="body2"
              component="pre"
              sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}
            >
              {`パッケージ名: @airone/plugin-hello-world
ID: hello-world-plugin
名前: Hello World Plugin
バージョン: 1.0.0
説明: プラグインシステムのデモ用サンプル
配布方法: 外部npmパッケージ
依存関係: @airone/core ^1.0.0`}
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
              プラグインAPI ステータス:
            </Typography>
            <Typography variant="body2">
              {pluginAPI
                ? "✅ プラグインAPIが利用可能です - 通知やナビゲーション機能が使用できます"
                : "⚠️ プラグインAPIが利用できません - 基本機能のみ動作します"}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default HelloWorldPage;
