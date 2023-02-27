import { Schema, schema } from "./UserFormSchema";

describe("schema", () => {
  // A valid value
  const baseValue: Schema = {
    username: "user1",
    email: "test@example.com",
    isSuperuser: false,
    password: "password",
  };

  test("validation succeeds for a valid value", () => {
    const value = { ...baseValue };
    expect(schema.parse(value)).toEqual(value);
  });

  test("validation fails if username is empty", () => {
    const value = {
      ...baseValue,
      username: "",
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if email is invalid", () => {
    const value = {
      ...baseValue,
      email: "just_a_string",
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if password is empty", () => {
    const value = {
      ...baseValue,
      password: "",
    };

    expect(() => schema.parse(value)).toThrow();
  });
});
