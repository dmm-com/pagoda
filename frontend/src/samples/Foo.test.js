/**
 * @jest-environment jsdom
 */

import { shallow } from "enzyme";
import React from "react";

import { Foo } from "./Foo";

it("unit test of Foo", () => {
  const wrapper = shallow(<Foo value={'hoge'}/>);
  
  expect(wrapper.state('data')).toEqual('hoge');

  console.log(wrapper.render().find('.in-foo'));
});
