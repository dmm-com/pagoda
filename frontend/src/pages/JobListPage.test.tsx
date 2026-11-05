/**
 */

import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { TestWrapper } from "TestWrapper";
import { JobListPage } from "pages/JobListPage";
import { ServerContext } from "services/ServerContext";

const server = setupServer(
  // getRoles
  http.get("http://localhost/job/api/v2/jobs", () => {
    return HttpResponse.json({
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          user: "user1",
          operation: 1,
          status: 1,
          passed_time: 1,
          created_at: new Date("2022-01-01T09:00:00.000000+09:00"),
          text: "note",
          target: {
            id: 1,
            name: "target1",
            schema_id: null,
            schema_name: null,
          },
        },
        {
          id: 2,
          user: "user2",
          operation: 2,
          status: 2,
          passed_time: 2,
          created_at: new Date("2022-01-01T09:00:00.000000+09:00"),
          text: "note",
          target: {
            id: 2,
            name: "target2",
            schema_id: null,
            schema_name: null,
          },
        },
      ],
    });
  }),
);

beforeAll(() => server.listen());

afterEach(() => {
  server.resetHandlers();
  vi.restoreAllMocks();
});

afterAll(() => server.close());

describe("JobListPage", () => {
  test("should match snapshot", async () => {
    let result: ReturnType<typeof render>;
    await act(async () => {
      result = render(<JobListPage />, {
        wrapper: TestWrapper,
      });
    });

    expect(result!).toMatchSnapshot();
  });

  test("submits a message filter to the job API", async () => {
    const searches: URL[] = [];
    let finishSearch: () => void = () => {};
    const searchPending = new Promise<void>((resolve) => {
      finishSearch = resolve;
    });
    render(<JobListPage />, { wrapper: TestWrapper });
    await screen.findByText("target1");
    server.use(
      http.get("http://localhost:3000/job/api/v2/jobs", async ({ request }) => {
        searches.push(new URL(request.url));
        await searchPending;
        return HttpResponse.json({
          count: 0,
          next: null,
          previous: null,
          results: [],
        });
      }),
    );

    fireEvent.change(screen.getByLabelText("備考・エラー文を部分検索"), {
      target: { value: "connection refused" },
    });
    fireEvent.click(screen.getByRole("button", { name: "検索" }));

    await waitFor(() => {
      expect(
        searches.some(
          (url) => url.searchParams.get("text") === "connection refused",
        ),
      ).toBe(true);
    });
    expect(screen.getByTestId("loading")).toBeInTheDocument();
    finishSearch();
    await waitFor(() => {
      expect(screen.queryByTestId("loading")).not.toBeInTheDocument();
    });
  }, 15_000);

  test("groups operations with the same label", async () => {
    const searches: URL[] = [];
    render(<JobListPage />, { wrapper: TestWrapper });
    await screen.findByText("target1");
    server.use(
      http.get("http://localhost:3000/job/api/v2/jobs", ({ request }) => {
        searches.push(new URL(request.url));
        return HttpResponse.json({
          count: 0,
          next: null,
          previous: null,
          results: [],
        });
      }),
    );

    fireEvent.mouseDown(screen.getByRole("combobox", { name: "操作" }));
    expect(
      screen.getAllByRole("option", { name: "エクスポート" }),
    ).toHaveLength(1);
    expect(screen.getAllByRole("option", { name: "編集" })).toHaveLength(1);
    fireEvent.click(screen.getByRole("option", { name: "エクスポート" }));
    fireEvent.click(screen.getByRole("button", { name: "検索" }));

    await waitFor(() => {
      expect(searches.length).toBeGreaterThan(0);
    });
    expect(searches.at(-1)?.searchParams.get("operation")?.split(",")).toEqual([
      "6",
      "8",
      "20",
      "22",
      "34",
    ]);
  });

  test("does not offer hidden jobs in a superuser search", async () => {
    vi.spyOn(ServerContext, "getInstance").mockReturnValue(
      new ServerContext({
        user: {
          id: 1,
          username: "admin",
          isSuperuser: true,
          isReadonly: false,
          parentUser: null,
          email: "admin@example.com",
        },
      }),
    );
    const searches: URL[] = [];
    render(<JobListPage />, { wrapper: TestWrapper });
    await screen.findByText("target1");
    server.use(
      http.get("http://localhost:3000/job/api/v2/jobs", ({ request }) => {
        searches.push(new URL(request.url));
        return HttpResponse.json({
          count: 0,
          next: null,
          previous: null,
          results: [],
        });
      }),
    );

    expect(
      screen.queryByRole("checkbox", { name: "内部ジョブのみ" }),
    ).toBeNull();
    expect(
      screen.queryByRole("checkbox", {
        name: "内部ジョブ・削除済み対象も含める",
      }),
    ).toBeNull();
    expect(
      screen.queryByRole("checkbox", { name: "説明欄が空の成功ジョブも表示" }),
    ).toBeNull();

    fireEvent.change(screen.getByLabelText("備考・エラー文を部分検索"), {
      target: { value: "internal" },
    });
    fireEvent.click(screen.getByRole("button", { name: "検索" }));

    await waitFor(() => {
      expect(
        searches.some((url) => url.searchParams.get("text") === "internal"),
      ).toBe(true);
    });
    for (const key of [
      "include_hidden",
      "internal_only",
      "include_empty_success",
    ]) {
      expect(searches.at(-1)?.searchParams.has(key)).toBe(false);
    }
  });
});
