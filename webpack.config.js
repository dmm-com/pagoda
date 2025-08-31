const path = require('path');
const ForkTsCheckerWebpackPlugin = require('fork-ts-checker-webpack-plugin');

module.exports = {
  entry: {
    index: "./frontend/src/App.tsx"
  },
  output: {
    filename: "ui.js",
    path: path.resolve('static/js')
  },
  resolve: {
    extensions: [".webpack.js", ".web.js", ".ts", ".tsx", ".js"],
    modules: [
      path.resolve('frontend/src'), 
      'node_modules'
    ],
    symlinks: true,
    alias: {
      'pagoda-plugin-hello-world': path.resolve(__dirname, 'node_modules/pagoda-plugin-hello-world'),
      'pagoda-plugin-dashboard': path.resolve(__dirname, 'node_modules/pagoda-plugin-dashboard'),
      'react': path.resolve(__dirname, 'node_modules/react'),
      'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
    }
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        include: [
          path.resolve('frontend/src')
        ],
        loader: 'ts-loader',
        options: {
          transpileOnly: true,
        }
      },
      {
        test: /\.ts$/,
        include: /node_modules\/@dmm-com\/airone-apiclient-typescript-fetch/,
        loader: 'ts-loader',
        options: {
          transpileOnly: true,
        }
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        include: [
          path.resolve('frontend/src')
        ],
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
            plugins: ['@babel/plugin-transform-runtime'],
          },
        }
      },
      {
        test: /\.js$/,
        enforce: "pre",
        exclude: /node_modules\/clsx/,
        use: ["source-map-loader"],
      },
    ]
  },
  ignoreWarnings: [/Failed to parse source map/],
  plugins: [
    // Temporarily disabled to check if JS bundling works
    // new ForkTsCheckerWebpackPlugin()
  ]
};
