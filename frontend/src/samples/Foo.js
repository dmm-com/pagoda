import React from "react";
import { sendRequest } from "./APIClient";

export class Foo extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      data: props.value,
    }
  }

  handleSubmit(event) {
    sendRequest(this.state.data);
  };

  render() {
    const { data } = this.state;

    return (
      <form onSubmit={this.handleSubmit.bind(this)}>
        <textarea
          value={ data }
          onChange={(e) => this.setState({data: e.target.value})}
        />
      </form>
    );
  }
}
