const path = require('path');

module.exports = {
  entry: {
    index: "./frontend/src/App.js"
  },
  output: {
    filename: "new-ui.js",
    path: path.resolve('static/js')
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
