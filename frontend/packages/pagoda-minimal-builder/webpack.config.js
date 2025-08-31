const path = require("path");

module.exports = {
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
    alias: {
      'pagoda-plugin-hello-world': path.resolve(__dirname, 'node_modules/pagoda-plugin-hello-world'),
      'pagoda-plugin-dashboard': path.resolve(__dirname, 'node_modules/pagoda-plugin-dashboard'),
      'react': path.resolve(__dirname, 'node_modules/react'),
      'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
    },
  },
  devServer: {
    static: {
      directory: path.join(__dirname, "dist"),
    },
    port: 3000,
  },
};
