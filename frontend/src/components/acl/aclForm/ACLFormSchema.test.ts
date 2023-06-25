/**
 * @jest-environment jsdom
 */

import { Schema, schema } from "./ACLFormSchema";

beforeAll(() => {
  Object.defineProperty(window, "django_context", {
    value: {
      version: "v0.0.1-test",
      user: {
        id: 123,
        isSuperuser: true,
      },
    },
    writable: false,
  });
});

describe("schema", () => {
  const baseValue: Schema = {
    isPublic: false,
    defaultPermission: 2, // readable
    objtype: 1,
    roles: [
      {
        id: 1,
        name: "role1",
        description: "role1",
        currentPermission: 8, // full
      },
    ],
  };

  test("validation succeeds for a valid value", () => {
    const value = { ...baseValue };
    expect(schema.parse(value)).toEqual(value);
  });

  test("validation fails if anyone doesn't have full permission", () => {
    const value = {
      ...baseValue,
      roles: [
        {
          id: 1,
          name: "role1",
          description: "role1",
          currentPermission: 2, // readable
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });
});
