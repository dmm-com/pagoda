/**
 * @jest-environment jsdom
 */

import { act, render } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { TestWrapper } from "TestWrapper";
import { GroupListPage } from "pages/GroupListPage";

const server = setupServer(
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
);

beforeAll(() => server.listen());

afterEach(() => server.resetHandlers());

afterAll(() => server.close());

describe("GroupListPage", () => {
  test("should match snapshot", async () => {
    Object.defineProperty(window, "django_context", {
      value: {
        user: {
          isSuperuser: true,
        },
      },
      writable: false,
    });

    let result: ReturnType<typeof render>;
    await act(async () => {
      result = render(<GroupListPage />, {
        wrapper: TestWrapper,
      });
    });

    expect(result!).toMatchSnapshot();
  });
});
