/**
 * @jest-environment jsdom
 */

import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";
import { render, screen } from "@testing-library/react";

import { EntityBreadcrumbs } from "./EntityBreadcrumbs";

import { TestWrapper } from "TestWrapper";

// Mock the routes functions
jest.mock("routes/Routes", () => ({
  topPath: jest.fn().mockReturnValue("/"),
  entitiesPath: jest.fn().mockReturnValue("/entities"),
  entityEntriesPath: jest.fn().mockReturnValue("/entity/1/entries"),
}));

describe("EntityBreadcrumbs", () => {
  const mockEntity: EntityDetail = {
    id: 1,
    name: "Test Entity",
    note: "",
    isPublic: true,
    isToplevel: false,
    hasOngoingChanges: false,
    attrs: [],
    webhooks: [],
  };

  test("renders basic breadcrumbs without entity, attr, or title", () => {
    render(<EntityBreadcrumbs />, { wrapper: TestWrapper });

    // Check if basic navigation links are rendered
    expect(screen.getByText("Top")).toBeInTheDocument();
    expect(screen.getByText("モデル一覧")).toBeInTheDocument();

    // Entity, attr, and title should not be rendered
    expect(screen.queryByText("Test Entity")).not.toBeInTheDocument();
  });

  test("renders breadcrumbs with entity", () => {
    render(<EntityBreadcrumbs entity={mockEntity} />, { wrapper: TestWrapper });

    // Check if all expected elements are rendered
    expect(screen.getByText("Top")).toBeInTheDocument();
    expect(screen.getByText("モデル一覧")).toBeInTheDocument();
    expect(screen.getByText("Test Entity")).toBeInTheDocument();
  });

  test("renders lock icon for non-public entity", () => {
    const privateEntity = { ...mockEntity, isPublic: false };
    const { container } = render(<EntityBreadcrumbs entity={privateEntity} />, {
      wrapper: TestWrapper,
    });

    // Check if lock icon is rendered
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  test("renders breadcrumbs with entity and attr", () => {
    render(<EntityBreadcrumbs entity={mockEntity} attr="Test Attribute" />, {
      wrapper: TestWrapper,
    });

    // Check if all expected elements are rendered
    expect(screen.getByText("Top")).toBeInTheDocument();
    expect(screen.getByText("モデル一覧")).toBeInTheDocument();
    expect(screen.getByText("Test Entity")).toBeInTheDocument();
    expect(screen.getByText("Test Attribute")).toBeInTheDocument();
  });

  test("renders breadcrumbs with entity, attr, and title", () => {
    render(
      <EntityBreadcrumbs
        entity={mockEntity}
        attr="Test Attribute"
        title="Test Title"
      />,
      { wrapper: TestWrapper },
    );

    // Check if all expected elements are rendered
    expect(screen.getByText("Top")).toBeInTheDocument();
    expect(screen.getByText("モデル一覧")).toBeInTheDocument();
    expect(screen.getByText("Test Entity")).toBeInTheDocument();
    expect(screen.getByText("Test Attribute")).toBeInTheDocument();
    expect(screen.getByText("Test Title")).toBeInTheDocument();
  });

  test("links have correct hrefs", () => {
    render(<EntityBreadcrumbs entity={mockEntity} />, { wrapper: TestWrapper });

    // Check if links have correct hrefs
    const topLink = screen.getByText("Top").closest("a");
    const entitiesLink = screen.getByText("モデル一覧").closest("a");
    const entityLink = screen.getByText("Test Entity").closest("a");

    expect(topLink).toHaveAttribute("href", "/");
    expect(entitiesLink).toHaveAttribute("href", "/entities");
    expect(entityLink).toHaveAttribute("href", "/entity/1/entries");
  });
});
