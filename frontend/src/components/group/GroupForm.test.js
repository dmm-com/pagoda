/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import { shallow } from "enzyme";
import React from "react";

/* create mock processings of AirOneAPIClient to prevent sending requests */
jest.mock("../../utils/AironeAPIClient", () => {
  return {
    createGroup: jest.fn().mockImplementation((name, members) => {
      testContext = {
        createGroupIsCalled: true,
        name: name,
        members: members,
      };

      return Promise.resolve({});
    }),
    updateGroup: jest.fn().mockImplementation((group_id, name, members) => {
      testContext = {
        updateGroupIsCalled: true,
        group_id: group_id,
        name: name,
        members: members,
      };

      return Promise.resolve({});
    }),
  };
});
import { GroupForm } from "./GroupForm";

let testContext;
beforeEach(() => {
  /* rest textContext */
  testContext = {};
});

describe("test for GrouForm component", () => {
  const TestUsers = [
    { id: 10, username: "userA" },
    { id: 11, username: "userB" },
    { id: 12, username: "userC" },
  ];

  it("check initial state variables", () => {
    const wrapper = shallow(
      <GroupForm
        users={TestUsers}
        group={{ id: 10, name: "groupname", members: TestUsers }}
      />
    );

    expect(wrapper.state("name")).toEqual("groupname");
    expect(wrapper.state("members")).toEqual([10, 11, 12]);
  });

  it("check initial state variables without specifying group parameter", () => {
    const wrapper = shallow(<GroupForm users={TestUsers} />);

    expect(wrapper.state("name")).toEqual("");
    expect(wrapper.state("members")).toEqual([]);
  });

  it("submit to create new Group instance", () => {
    const wrapper = shallow(<GroupForm users={TestUsers} />);

    /* set state variables of GroupForm component */
    wrapper.setState({
      name: "newGroupName",
      members: [20, 21],
    });

    /* simulate to submit request form */
    wrapper.find("form").simulate("submit", {
      preventDefault: jest.fn().mockReturnValue(),
    });

    expect(testContext).toEqual({
      createGroupIsCalled: true,
      name: "newGroupName",
      members: [20, 21],
    });
  });

  it("submit to udpate existed Group instance", () => {
    const wrapper = shallow(
      <GroupForm
        users={TestUsers}
        group={{ id: 10, name: "groupname", members: TestUsers }}
      />
    );

    /* set state variables of GroupForm component */
    wrapper.setState({
      name: "newGroupName",
      members: [20, 21],
    });

    /* simulate to submit request form */
    wrapper.find("form").simulate("submit", {
      preventDefault: jest.fn().mockReturnValue(),
    });

    expect(testContext).toEqual({
      updateGroupIsCalled: true,
      group_id: 10,
      name: "newGroupName",
      members: [20, 21],
    });
  });
});
