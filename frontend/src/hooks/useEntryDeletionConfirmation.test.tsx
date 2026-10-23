import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { useEntryDeletionConfirmation } from "./useEntryDeletionConfirmation";

import { aironeApiClient } from "repository/AironeApiClient";

vi.mock("repository/AironeApiClient", () => ({
  aironeApiClient: { getEntryReferral: vi.fn() },
}));

const onDelete = vi.fn();
const reference = {
  id: 2,
  name: "server1",
  schema: { id: 10, name: "Server" },
};
const Harness = ({
  ids = [1],
  confirmationTitle,
  entryNames,
}: {
  ids?: number[];
  confirmationTitle?: string;
  entryNames?: Record<number, string>;
}) => {
  const { confirmEntryDeletion, deletionConfirmationDialog } =
    useEntryDeletionConfirmation();
  return (
    <>
      <button
        onClick={async () => {
          if (await confirmEntryDeletion(ids, confirmationTitle, entryNames))
            onDelete();
        }}
      >
        delete
      </button>
      {deletionConfirmationDialog}
    </>
  );
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(aironeApiClient.getEntryReferral).mockResolvedValue({
    count: 0,
    results: [],
  });
});

test("continues immediately when no other items reference the targets", async () => {
  render(<Harness ids={[1, 3, 1]} />);
  fireEvent.click(screen.getByText("delete"));
  await waitFor(() => expect(onDelete).toHaveBeenCalledOnce());
  expect(aironeApiClient.getEntryReferral).toHaveBeenCalledTimes(2);
  expect(aironeApiClient.getEntryReferral).toHaveBeenNthCalledWith(2, 3, 1);
});

test("shows incoming references and requires an explicit decision", async () => {
  vi.mocked(aironeApiClient.getEntryReferral).mockResolvedValue({
    count: 101,
    results: [reference],
  } as Awaited<ReturnType<typeof aironeApiClient.getEntryReferral>>);
  render(<Harness entryNames={{ 1: "network1" }} />);
  fireEvent.click(screen.getByText("delete"));
  expect(
    await screen.findByRole("link", { name: "Server / server1" }),
  ).toHaveAttribute("href", "/ui/entities/10/entries/2/details");
  expect(screen.getByText(/101/)).toBeInTheDocument();
  expect(screen.getByText(/network1/)).toBeInTheDocument();
  expect(screen.queryByText(/#1:/)).not.toBeInTheDocument();
  expect(onDelete).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "影響を理解して削除" }));
  await waitFor(() => expect(onDelete).toHaveBeenCalledOnce());
});

test("cancelling the warning does not delete and reopening checks fresh references", async () => {
  vi.mocked(aironeApiClient.getEntryReferral).mockResolvedValue({
    count: 1,
    results: [reference],
  } as Awaited<ReturnType<typeof aironeApiClient.getEntryReferral>>);
  render(<Harness />);
  fireEvent.click(screen.getByText("delete"));
  await screen.findByRole("link", { name: "Server / server1" });
  fireEvent.click(screen.getByRole("button", { name: "キャンセル" }));
  await waitFor(() =>
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
  );
  expect(onDelete).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText("delete"));
  await screen.findByRole("link", { name: "Server / server1" });
  expect(aironeApiClient.getEntryReferral).toHaveBeenCalledTimes(2);
});

test("does not delete any targets when one reference check fails", async () => {
  vi.mocked(aironeApiClient.getEntryReferral)
    .mockResolvedValueOnce({ count: 0, results: [] })
    .mockRejectedValueOnce(new Error("offline"));
  render(<Harness ids={[1, 3]} />);
  fireEvent.click(screen.getByText("delete"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "削除は実行していません",
  );
  expect(
    screen.queryByRole("button", { name: "影響を理解して削除" }),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "キャンセル" }));
  expect(onDelete).not.toHaveBeenCalled();
});

test("ignores an item's reference to itself", async () => {
  vi.mocked(aironeApiClient.getEntryReferral).mockResolvedValue({
    count: 1,
    results: [{ ...reference, id: 1 }],
  } as Awaited<ReturnType<typeof aironeApiClient.getEntryReferral>>);
  render(<Harness />);
  fireEvent.click(screen.getByText("delete"));
  await waitFor(() => expect(onDelete).toHaveBeenCalledOnce());
});

test("cancelling during a pending check cannot lead to deletion", async () => {
  let resolveCheck!: (value: { count: number; results: [] }) => void;
  vi.mocked(aironeApiClient.getEntryReferral).mockReturnValue(
    new Promise((resolve) => {
      resolveCheck = resolve;
    }),
  );
  render(<Harness />);
  fireEvent.click(screen.getByText("delete"));
  fireEvent.click(await screen.findByRole("button", { name: "キャンセル" }));
  resolveCheck({ count: 0, results: [] });
  await waitFor(() =>
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
  );
  expect(onDelete).not.toHaveBeenCalled();
});

test("shows only the standard confirmation when there are no incoming references", async () => {
  render(<Harness confirmationTitle="本当に削除しますか？" />);
  fireEvent.click(screen.getByText("delete"));
  expect(await screen.findByText("本当に削除しますか？")).toBeInTheDocument();
  expect(
    screen.queryByText("参照されているアイテムの削除"),
  ).not.toBeInTheDocument();
  expect(onDelete).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Yes" }));
  await waitFor(() => expect(onDelete).toHaveBeenCalledOnce());
});

test("skips the standard confirmation when incoming references exist", async () => {
  vi.mocked(aironeApiClient.getEntryReferral).mockResolvedValue({
    count: 1,
    results: [reference],
  } as Awaited<ReturnType<typeof aironeApiClient.getEntryReferral>>);
  render(<Harness confirmationTitle="本当に削除しますか？" />);
  fireEvent.click(screen.getByText("delete"));
  await screen.findByRole("link", { name: "Server / server1" });
  expect(screen.queryByText("本当に削除しますか？")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Yes" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "影響を理解して削除" }));
  await waitFor(() => expect(onDelete).toHaveBeenCalledOnce());
});

test("cancelling the standard confirmation leaves the item intact", async () => {
  render(<Harness confirmationTitle="本当に削除しますか？" />);
  fireEvent.click(screen.getByText("delete"));
  fireEvent.click(await screen.findByRole("button", { name: "No" }));
  await waitFor(() =>
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
  );
  expect(onDelete).not.toHaveBeenCalled();
});
