const path = require('path');

module.exports = {
  entry: {
    index: "./frontend/src/index.js"
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
          loader: "babel-loader"
        }
      }
    ]
  }
};
