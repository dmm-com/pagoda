/**
 * @jest-environment jsdom
 */

import { render } from "@testing-library/react";
import React from "react";

import { ACLForm } from "./ACLForm";

test("should render a component with essential props", function () {
  const acl = {
    name: "entity1",
    is_public: true,
    acltypes: [
      {
        id: 1,
        name: "Nothing",
      },
      {
        id: 2,
        name: "Full Controllable",
      },
    ],
    members: [
      {
        name: "admin",
        current_permission: 1,
      },
    ],
  };
  expect(() => render(<ACLForm objectId={1} acl={acl} />)).not.toThrow();
});
