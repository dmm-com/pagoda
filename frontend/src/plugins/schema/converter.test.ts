import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";

import { toEntityStructure } from "./converter";
import { AttrType } from "./types";

/**
 * Helper to create a valid EntityDetail for testing.
 * Provides default values for all required fields.
 */
function createEntityDetail(
  partial: Partial<EntityDetail> & Pick<EntityDetail, "id" | "name" | "attrs">,
): EntityDetail {
  return {
    note: "",
    isToplevel: false,
    webhooks: [],
    isPublic: true,
    hasOngoingChanges: false,
    permission: 0,
    ...partial,
  };
}

/**
 * Helper to create a valid EntityDetailAttribute for testing.
 */
function createAttr(partial: {
  id: number;
  name: string;
  type: number;
  isMandatory?: boolean;
  referral?: { id: number; name: string }[];
}) {
  return {
    index: 0,
    isDeleteInChain: false,
    isWritable: true,
    isSummarized: false,
    note: "",
    isMandatory: false,
    referral: [],
    ...partial,
  };
}

describe("toEntityStructure", () => {
  it("should convert basic entity structure", () => {
    const apiEntity = createEntityDetail({
      id: 1,
      name: "NetworkDevice",
      note: "Network device entity",
      isToplevel: true,
      attrs: [
        createAttr({
          id: 101,
          name: "hostname",
          type: AttrType.STRING,
          isMandatory: true,
        }),
      ],
    });

    const result = toEntityStructure(apiEntity);

    expect(result).toEqual({
      id: 1,
      name: "NetworkDevice",
      attrs: [
        {
          id: 101,
          name: "hostname",
          type: AttrType.STRING,
          isMandatory: true,
          referral: [],
        },
      ],
    });
  });

  it("should convert entity with referral attributes", () => {
    const apiEntity = createEntityDetail({
      id: 1,
      name: "Server",
      attrs: [
        createAttr({
          id: 201,
          name: "location",
          type: AttrType.OBJECT,
          referral: [
            { id: 10, name: "Datacenter" },
            { id: 11, name: "Office" },
          ],
        }),
      ],
    });

    const result = toEntityStructure(apiEntity);

    expect(result.attrs[0].referral).toEqual([
      { id: 10, name: "Datacenter" },
      { id: 11, name: "Office" },
    ]);
  });

  it("should handle entity with multiple attributes", () => {
    const apiEntity = createEntityDetail({
      id: 2,
      name: "Application",
      isToplevel: true,
      attrs: [
        createAttr({
          id: 301,
          name: "name",
          type: AttrType.STRING,
          isMandatory: true,
        }),
        createAttr({ id: 302, name: "version", type: AttrType.STRING }),
        createAttr({ id: 303, name: "port", type: AttrType.NUMBER }),
        createAttr({ id: 304, name: "enabled", type: AttrType.BOOLEAN }),
      ],
    });

    const result = toEntityStructure(apiEntity);

    expect(result.attrs).toHaveLength(4);
    expect(result.attrs.map((a) => a.name)).toEqual([
      "name",
      "version",
      "port",
      "enabled",
    ]);
    expect(result.attrs.map((a) => a.type)).toEqual([
      AttrType.STRING,
      AttrType.STRING,
      AttrType.NUMBER,
      AttrType.BOOLEAN,
    ]);
  });

  it("should handle entity with no attributes", () => {
    const apiEntity = createEntityDetail({
      id: 3,
      name: "EmptyEntity",
      attrs: [],
    });

    const result = toEntityStructure(apiEntity);

    expect(result).toEqual({
      id: 3,
      name: "EmptyEntity",
      attrs: [],
    });
  });

  it("should handle undefined referral by defaulting to empty array", () => {
    // Simulate API response where referral might be undefined
    const apiEntity = createEntityDetail({
      id: 4,
      name: "TestEntity",
      attrs: [
        {
          id: 401,
          name: "someAttr",
          type: AttrType.STRING,
          isMandatory: false,
          index: 0,
          isDeleteInChain: false,
          isWritable: true,
          isSummarized: false,
          note: "",
          referral: undefined as unknown as [],
        },
      ],
    });

    const result = toEntityStructure(apiEntity);

    expect(result.attrs[0].referral).toEqual([]);
  });

  it("should handle array type attributes", () => {
    const apiEntity = createEntityDetail({
      id: 5,
      name: "ArrayEntity",
      attrs: [
        createAttr({ id: 501, name: "tags", type: AttrType.ARRAY_STRING }),
        createAttr({
          id: 502,
          name: "servers",
          type: AttrType.ARRAY_OBJECT,
          referral: [{ id: 100, name: "Server" }],
        }),
      ],
    });

    const result = toEntityStructure(apiEntity);

    expect(result.attrs[0].type).toBe(AttrType.ARRAY_STRING);
    expect(result.attrs[1].type).toBe(AttrType.ARRAY_OBJECT);
    expect(result.attrs[1].referral).toEqual([{ id: 100, name: "Server" }]);
  });

  it("should strip extra fields from API response", () => {
    const apiEntity = createEntityDetail({
      id: 6,
      name: "FullEntity",
      note: "This note should be stripped",
      isToplevel: true,
      isPublic: false,
      attrs: [
        createAttr({
          id: 601,
          name: "field",
          type: AttrType.STRING,
          isMandatory: true,
        }),
      ],
    });

    const result = toEntityStructure(apiEntity);

    // Result should only have id, name, attrs
    expect(Object.keys(result)).toEqual(["id", "name", "attrs"]);

    // Attr should only have id, name, type, isMandatory, referral
    expect(Object.keys(result.attrs[0])).toEqual([
      "id",
      "name",
      "type",
      "isMandatory",
      "referral",
    ]);
  });

  it("should preserve isMandatory flag correctly", () => {
    const apiEntity = createEntityDetail({
      id: 7,
      name: "MandatoryTest",
      attrs: [
        createAttr({
          id: 701,
          name: "required",
          type: AttrType.STRING,
          isMandatory: true,
        }),
        createAttr({
          id: 702,
          name: "optional",
          type: AttrType.STRING,
          isMandatory: false,
        }),
      ],
    });

    const result = toEntityStructure(apiEntity);

    expect(result.attrs[0].isMandatory).toBe(true);
    expect(result.attrs[1].isMandatory).toBe(false);
  });
});
