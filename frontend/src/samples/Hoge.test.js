import { shallow } from "enzyme";
import React from "react";

jest.mock('./APIClient', () => {
  return {
    sendRequest: jest.fn().mockImplementation((data) => {
      /* set test data to confirm sendRequest() is called */
      _testContext = {
        sendRequest: {
          isCalled: true,
          args: [data],
        }
      }
    })
  }
});
import { Hoge } from "./Hoge";
import { Foo } from "./Foo";

let _testContext;
beforeEach(() => {
  /* rest textContext */
  _testContext = {};
});

it("unit test of Hoge", () => {
  const wrapper = shallow(<Hoge value={'hoge'}/>);

  /* check render context of Hoge component */
  expect(wrapper.render().find('.in-hoge')).toHaveLength(1);
  expect(wrapper.render().find('.form-title').text()).toEqual('input title');

  /* Enzyme has a regulation not to be able to get state variable using Hooks */
  // expect(wrapper.state('data')).toEqual('hoge');

  /* simulate to submit form */
  wrapper.find('form').simulate('submit');

  /* This checks result of mock event-handler processing */
  expect(_testContext.sendRequest.isCalled).toBeTruthy();
  expect(_testContext.sendRequest.args).toEqual(['hoge']);
});


it("unit test of Foo", () => {
  const wrapper = shallow(<Foo value={'hoge'}/>);

  /* check value of state variables */
  expect(wrapper.state('data')).toEqual('hoge');

  /* simulate to submit form with changing state variable */
  wrapper.setState({data: 'fuga'});
  wrapper.find('form').simulate('submit');

  /* This checks result of mock event-handler processing */
  expect(_testContext.sendRequest.isCalled).toBeTruthy();
  expect(_testContext.sendRequest.args).toEqual(['fuga']);
});
