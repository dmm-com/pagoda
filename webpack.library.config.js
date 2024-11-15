const path = require('path');

module.exports = {
  mode: 'production',
  entry: './frontend/src/index.ts',
  output: {
    path: path.resolve(__dirname, 'frontend/dist'),
    filename: 'pagoda-core.js',
    library: {
      name: 'Pagoda Core Module',
      type: 'umd',
    },
    globalObject: 'this',
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        exclude: /node_modules/,
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
    ],
  },
  resolve: {
    extensions: [".webpack.js", ".web.js", ".ts", ".tsx", ".js"],
    modules: [
      path.resolve(__dirname, 'frontend/src'),
      'node_modules',
    ],
  },
  externals: ['react', 'react-dom'],
} 