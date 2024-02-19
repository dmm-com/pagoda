/**
 * @jest-environment jsdom
 */

import {
  render,
  waitForElementToBeRemoved,
  screen,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import React from "react";

import { TestWrapper } from "TestWrapper";
import { GroupEditPage } from "pages/GroupEditPage";

const server = setupServer(
  // getGroup
  http.get("http://localhost/group/api/v2/groups/1", () => {
    return HttpResponse.json({
      id: 1,
      name: "group1",
      members: [
        {
          id: 1,
          username: "user1",
        },
      ],
      parent_group: null,
    });
  }),
  // getGroupTrees
  http.get("http://localhost/group/api/v2/groups/tree", () => {
    return HttpResponse.json([
      {
        id: 1,
        name: "group1",
        children: [
          {
            id: 1,
            name: "group1",
            children: [],
          },
          {
            id: 2,
            name: "group2",
            children: [],
          },
        ],
      },
      {
        id: 2,
        name: "group2",
        children: [],
      },
    ]);
  }),
  // getUsers
  http.get("http://localhost/user/api/v2/", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          username: "user1",
          email: "user1@example.com",
          is_superuser: false,
        },
        {
          id: 2,
          username: "user2",
          email: "user2@example.com",
          is_superuser: false,
        },
      ],
    });
  })
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("EditGroupPage", () => {
  Object.defineProperty(window, "django_context", {
    value: {
      user: {
        isSuperuser: true,
      },
    },
    writable: false,
  });

  test("should match snapshot", async () => {
    // wait async calls and get rendered fragment
    const result = render(<GroupEditPage />, {
      wrapper: TestWrapper,
    });
    await waitForElementToBeRemoved(screen.getByTestId("loading"));

    expect(result).toMatchSnapshot();
  });
});
