import path from "path";
import { fileURLToPath } from "url";
import pluginsConfig from "./plugins.config.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Dynamically generate webpack aliases from plugin configuration
const generatePluginAliases = () => {
  const aliases = {
    react: path.resolve(__dirname, "node_modules/react"),
    "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
  };

  // Add alias for each configured plugin
  pluginsConfig.plugins.forEach((pluginName) => {
    aliases[pluginName] = path.resolve(__dirname, "node_modules", pluginName);
  });

  return aliases;
};

export default {
  entry: "./src/App.tsx",
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "ui.js",
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        loader: "ts-loader",
        options: {
          transpileOnly: true,
        },
      },
    ],
  },
  resolve: {
    extensions: [".webpack.js", ".web.js", ".ts", ".tsx", ".js"],
    modules: [path.resolve(__dirname, "src"), "node_modules"],
    symlinks: true,
    alias: generatePluginAliases(),
  },
  devServer: {
    static: {
      directory: path.join(__dirname, "dist"),
    },
    port: 3000,
  },
};
