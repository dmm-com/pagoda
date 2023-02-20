import { Schema, schema } from "./RoleFormSchema";

describe("schema", () => {
  // A valid value
  const baseValue: Schema = {
    id: 1,
    isActive: true,
    name: "role1",
    description: "test description",
    users: [
      {
        id: 1,
        username: "user1",
      },
      {
        id: 2,
        username: "user2",
      },
    ],
    groups: [
      {
        id: 1,
        name: "group1",
      },
      {
        id: 2,
        name: "group2",
      },
    ],
    adminUsers: [
      {
        id: 3,
        username: "user3",
      },
      {
        id: 4,
        username: "user4",
      },
    ],
    adminGroups: [
      {
        id: 3,
        name: "group3",
      },
      {
        id: 4,
        name: "group4",
      },
    ],
  };

  test("validation succeeds for a valid value", () => {
    const value = { ...baseValue };
    expect(schema.parse(value)).toEqual(value);
  });

  test("validation fails if name is empty", () => {
    const value = {
      ...baseValue,
      name: "",
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if some users are also belonging to adminUsers", () => {
    const value = {
      ...baseValue,
      users: [
        {
          id: 1,
          username: "user1",
        },
        {
          id: 2,
          username: "user2",
        },
      ],
      adminUsers: [
        {
          id: 1,
          username: "user1",
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if some groups are also belonging to adminGroups", () => {
    const value = {
      ...baseValue,
      groups: [
        {
          id: 1,
          name: "group1",
        },
        {
          id: 2,
          name: "group2",
        },
      ],
      adminGroups: [
        {
          id: 1,
          name: "group1",
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if some adminUsers are also belonging to users", () => {
    const value = {
      ...baseValue,
      users: [
        {
          id: 3,
          username: "user3",
        },
      ],
      adminUsers: [
        {
          id: 3,
          username: "user3",
        },
        {
          id: 4,
          username: "user4",
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });

  test("validation fails if some adminGroups are also belonging to groups", () => {
    const value = {
      ...baseValue,
      groups: [
        {
          id: 3,
          name: "group3",
        },
      ],
      adminGroups: [
        {
          id: 3,
          name: "group3",
        },
        {
          id: 4,
          name: "group4",
        },
      ],
    };

    expect(() => schema.parse(value)).toThrow();
  });
});
