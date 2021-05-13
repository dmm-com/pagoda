import React, { Component } from "react";
import ReactDOM from "react-dom";
import PropTypes from 'prop-types'
import { Button } from '@material-ui/core';

import { withStyles } from '@material-ui/core/styles'

class _AppLayout extends Component {
  render() {
    const { classes } = this.props;

    return (
      <div className={ classes.container }>
        <div className={ classes.Header }>Header</div>
        <div className={ classes.LeftMenu }>Left Menu</div>
        <div className={ classes.MainContents }>Main</div>
        <div className={ classes.Footer }>Footer</div>
      </div>
    );
  }
};

const styles = {
  container: {
    display: "grid",
    "min-height": "100vh",
    "grid-template-rows": "100px 1fr 100px",
    "grid-template-columns": "100px 1fr",
  },
  Header: {
    "grid-row": "1",
    "grid-column": "1 / span 2",
    background: "#faa",
  },
  LeftMenu: {
    "grid-row": "2",
    "grid-column": "1",
    background: "#aaf",
  },
  MainContents: {
    "grid-row": "2",
    "grid-column": "2",
    background: "#afa",
  },
  Footer: {
    "grid-row": "3",
    "grid-column": "1 / span 2",
    background: "#aaa",
  },
  itemA: {
    "grid-row": "1 / 3",
    "grid-column": "1 / 2",
    background: "#f88",
  },
  itemB: {
    "grid-row": "1 / 2",
    "grid-column": "2 / 3",
    background: "#8f8",
  },
  itemC: {
    "grid-row": "2 / 3",
    "grid-column": "2 / 3",
    background: "#88f",
  }
}

let App = withStyles(styles)(_AppLayout);
ReactDOM.render(<App />, document.getElementById("app"));
