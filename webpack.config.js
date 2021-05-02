const glob = require('glob');
const path = require('path');

const entries = glob.sync('./react/src/**/*.jsx');
module.exports = {
  entry: entries,
  output: {
    path: path.resolve(__dirname, 'static', 'js', 'react'),
    filename: 'bundle.js',
    libraryTarget: 'umd',
  },
  module: {
    rules: [
      {
        test: /\.jsx/,
        exclude: /node_modules/,
        loader: 'babel-loader',
        options: {
          presets: ['@babel/preset-react']
        }
      },
    ]
  },
  resolve: {
    extensions: ['.js', '.jsx'],
  },
};