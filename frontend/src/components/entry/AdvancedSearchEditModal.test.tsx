/**
 */
import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import { AdvancedSearchEditModal } from "./AdvancedSearchEditModal";

import { TestWrapper } from "TestWrapper";
import i18n from "i18n/config";
import { aironeApiClient } from "repository/AironeApiClient";

vi.mock("hooks/usePagodaSWR", () => ({
  usePagodaSWR: () => ({ data: ["attrA", "attrB", "attrC"] }),
}));
vi.mock("react-router", async () => ({
  ...((await vi.importActual("react-router")) as object),
  useNavigate: () => vi.fn(),
}));

describe("AdvancedSearchEditModal", () => {
  test("submits an array attribute for selected items", async () => {
    await act(async () => {
      await i18n.changeLanguage("ja");
    });
    const referral = vi
      .spyOn(aironeApiClient, "getEntryReferral")
      .mockResolvedValue({ count: 0, results: [] });
    const attrs = vi
      .spyOn(aironeApiClient, "getEntityAttrs")
      .mockResolvedValue([
        {
          id: 10,
          name: "attrA",
          type: EntryAttributeTypeTypeEnum.ARRAY_STRING,
        },
      ]);
    const update = vi
      .spyOn(aironeApiClient, "bulkUpdateEntries")
      .mockResolvedValue();
    render(
      <AdvancedSearchEditModal
        openModal={true}
        handleClose={() => {}}
        modelIds={[1]}
        attrsFilter={{}}
        targetAttrID={10}
        targetAttrname="attrA"
        targetAttrtype={EntryAttributeTypeTypeEnum.ARRAY_STRING}
        selectedEntries={[{ id: 5, name: "更新アイテム", modelId: 1 }]}
      />,
      { wrapper: TestWrapper },
    );
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "更新" })).toBeEnabled(),
    );
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "new value" },
    });
    fireEvent.click(screen.getByRole("button", { name: "更新" }));
    await waitFor(() =>
      expect(update).toHaveBeenCalledWith(
        1,
        { id: 10, value: ["new value"] },
        [],
        "",
        undefined,
        [5],
      ),
    );
    referral.mockRestore();
    attrs.mockRestore();
    update.mockRestore();
  });

  test("updates every matching item when no checkbox is selected", async () => {
    await act(async () => {
      await i18n.changeLanguage("ja");
    });
    const search = vi
      .spyOn(aironeApiClient, "advancedSearch")
      .mockImplementation(
        async (_models, _attrs, _joins, _hasReferral, _referral, _all, page) =>
          ({
            count: 10,
            totalCount: 25,
            values: Array.from({ length: 10 }, (_, index) => ({
              entry: {
                id: (page - 1) * 10 + index + 1,
                name: `対象${(page - 1) * 10 + index + 1}`,
              },
              entity: { id: 1, name: "モデル" },
              attrs: {},
            })),
          }) as Awaited<ReturnType<typeof aironeApiClient.advancedSearch>>,
      );
    const referral = vi
      .spyOn(aironeApiClient, "getEntryReferral")
      .mockResolvedValue({ count: 0, results: [] });
    const attrs = vi
      .spyOn(aironeApiClient, "getEntityAttrs")
      .mockResolvedValue([{ id: 10, name: "attrA" }]);
    const update = vi
      .spyOn(aironeApiClient, "bulkUpdateEntries")
      .mockResolvedValue();
    render(
      <AdvancedSearchEditModal
        openModal={true}
        handleClose={() => {}}
        modelIds={[1]}
        attrsFilter={{}}
        targetAttrID={10}
        targetAttrname="attrA"
        targetAttrtype={EntryAttributeTypeTypeEnum.STRING}
        matchedCount={25}
      />,
      { wrapper: TestWrapper },
    );
    expect(
      await screen.findByText(
        "チェックがないため、検索条件に一致する全25件が変更対象です。",
      ),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", {
        name: "更新対象のアイテムと依存関係（25件）",
      }),
    );
    await screen.findByText("対象1");
    fireEvent.click(screen.getByRole("button", { name: "Go to page 2" }));
    await screen.findByText("対象11");
    expect(search).toHaveBeenCalledWith(
      [1],
      [],
      [],
      false,
      "",
      false,
      2,
      10,
      0,
      undefined,
    );
    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "changed" },
    });
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "更新" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "更新" }));
    await waitFor(() =>
      expect(update).toHaveBeenCalledWith(
        1,
        expect.anything(),
        [],
        "",
        undefined,
        undefined,
      ),
    );
    search.mockRestore();
    referral.mockRestore();
    attrs.mockRestore();
    update.mockRestore();
  });
  test("shows selected item names and their references before update", async () => {
    await act(async () => {
      await i18n.changeLanguage("ja");
    });
    const referral = vi
      .spyOn(aironeApiClient, "getEntryReferral")
      .mockResolvedValue({
        count: 1,
        results: [
          {
            id: 20,
            name: "依存アイテム",
            schema: { id: 3, name: "参照モデル" },
          },
        ],
      });
    render(
      <AdvancedSearchEditModal
        openModal={true}
        handleClose={() => {}}
        modelIds={[1]}
        attrsFilter={{}}
        targetAttrID={10}
        targetAttrname="attrA"
        targetAttrtype={EntryAttributeTypeTypeEnum.STRING}
        selectedEntries={[{ id: 5, name: "更新アイテム", modelId: 1 }]}
      />,
      { wrapper: TestWrapper },
    );
    const targetSummary = screen.getByRole("button", {
      name: "更新対象のアイテムと依存関係（1件）",
    });
    expect(targetSummary).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(targetSummary);
    expect(screen.getByText("更新アイテム")).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "参照元: 1件" }));
    expect(
      await screen.findByRole("link", { name: "参照モデル / 依存アイテム" }),
    ).toBeInTheDocument();
    expect(referral).toHaveBeenCalledWith(5, 1);
    referral.mockRestore();
  });

  test("shows large target lists ten at a time", async () => {
    await act(async () => {
      await i18n.changeLanguage("ja");
    });
    const referral = vi
      .spyOn(aironeApiClient, "getEntryReferral")
      .mockResolvedValue({ count: 0, results: [] });
    render(
      <AdvancedSearchEditModal
        openModal={true}
        handleClose={() => {}}
        modelIds={[1]}
        attrsFilter={{}}
        targetAttrID={10}
        targetAttrname="attrA"
        targetAttrtype={EntryAttributeTypeTypeEnum.STRING}
        selectedEntries={Array.from({ length: 11 }, (_, index) => ({
          id: index + 1,
          name: `対象${index + 1}`,
          modelId: 1,
        }))}
      />,
      { wrapper: TestWrapper },
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: "更新対象のアイテムと依存関係（11件）",
      }),
    );
    expect(screen.getByText("対象1")).toBeInTheDocument();
    expect(screen.queryByText("対象11")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Go to page 2" }));
    expect(screen.getByText("対象11")).toBeInTheDocument();
    expect(screen.queryByText("対象1")).not.toBeInTheDocument();
    referral.mockRestore();
  });
  test("should render modal with title and buttons", () => {
    render(
      <AdvancedSearchEditModal
        openModal={true}
        handleClose={() => {}}
        modelIds={[1]}
        attrsFilter={{}}
        targetAttrID={10}
        targetAttrname={"attrA"}
        targetAttrtype={EntryAttributeTypeTypeEnum.STRING}
      />,
      { wrapper: TestWrapper },
    );
    expect(
      screen.getByText("一括更新する（変更後の）値に更新"),
    ).toBeInTheDocument();
    expect(screen.getByText("属性「attrA」の変更後の値")).toBeInTheDocument();
    expect(screen.getByText("更新")).toBeInTheDocument();
    expect(screen.getByText("キャンセル")).toBeInTheDocument();
  });

  test("renders in English", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });
    render(
      <AdvancedSearchEditModal
        openModal={true}
        handleClose={() => {}}
        modelIds={[1]}
        attrsFilter={{}}
        targetAttrID={10}
        targetAttrname={"attrA"}
        targetAttrtype={EntryAttributeTypeTypeEnum.STRING}
      />,
      { wrapper: TestWrapper },
    );
    expect(
      screen.getByText("Update to the (changed) value for bulk update"),
    ).toBeInTheDocument();
    expect(
      screen.getByText('New value for attribute "attrA"'),
    ).toBeInTheDocument();
    expect(screen.getByText("Update")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });
});
