/**
 */

import { act } from "@testing-library/react";

import { Schema, schema } from "./ACLFormSchema";

import i18n from "i18n/config";

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

  test("validation error message is in Japanese by default", () => {
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

    try {
      schema.parse(value);
      fail("should have thrown");
    } catch (e) {
      expect(String(e)).toContain(
        "限定公開にする場合は、いずれかのロールの権限を 閲覧・編集・削除 にしてください",
      );
    }
  });

  test("validation error message is in English when language is switched", async () => {
    await act(async () => {
      await i18n.changeLanguage("en");
    });

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

    try {
      schema.parse(value);
      fail("should have thrown");
    } catch (e) {
      expect(String(e)).toContain(
        "To set this to limited public, set at least one role's permission to Read / Write / Delete",
      );
    }

    await act(async () => {
      await i18n.changeLanguage("ja");
    });
  });
});
