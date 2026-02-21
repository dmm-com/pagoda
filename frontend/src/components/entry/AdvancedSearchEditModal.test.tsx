/**
 * @jest-environment jsdom
 */
import { EntryAttributeTypeTypeEnum } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen } from "@testing-library/react";

import { AdvancedSearchEditModal } from "./AdvancedSearchEditModal";

import { TestWrapper } from "TestWrapper";

jest.mock("hooks/usePagodaSWR", () => ({
  usePagodaSWR: () => ({ data: ["attrA", "attrB", "attrC"] }),
}));
jest.mock("react-router", () => ({
  ...jest.requireActual("react-router"),
  useNavigate: () => jest.fn(),
}));

describe("AdvancedSearchEditModal", () => {
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
    expect(screen.getByText("更新")).toBeInTheDocument();
    expect(screen.getByText("キャンセル")).toBeInTheDocument();
  });
});
