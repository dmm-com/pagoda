const path = require('path');

module.exports = {
  entry: {
    index: "./frontend/src/App.js"
  },
  output: {
    filename: "main.js",
    path: path.resolve('templates/frontend')
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
            plugins: ['@babel/plugin-transform-runtime'],
          },
        }
      }
    ]
  }
};
