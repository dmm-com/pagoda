const path = require('path');

module.exports = {
  entry: {
    index: "./frontend/src/App.tsx"
  },
  output: {
    filename: "new-ui.js",
    path: path.resolve('static/js')
  },
  resolve: {
    extensions: [".webpack.js", ".web.js", ".ts", ".tsx", ".js"],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        use: 'ts-loader',
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
            plugins: ['@babel/plugin-transform-runtime'],
          },
        }
      }
    ]
  }
};

if (process.env.NODE_ENV !== 'production') {
  module.exports.devtool = 'inline-source-map';
}
