/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { EntityForm } from "components/entity/EntityForm";
import { TestWrapper } from "utils/TestWrapper";

test("should render a component with essential props", function () {
  expect(() =>
    render(
      <EntityForm
        entityInfo={{
          name: "hoge",
          note: "fuga",
          isTopLevel: false,
          attributes: [],
          webhooks: [],
        }}
        setEntityInfo={(d) => {
          /* no operation */
        }}
        referralEntities={[]}
        setSubmittable={(b) => {
          /* no operation */
        }}
      />,
      {
        wrapper: TestWrapper,
      }
    )
  ).not.toThrow();
});
