import { EntityDetail } from "@dmm-com/airone-apiclient-typescript-fetch";

import { toAttrRecord } from "./converter";
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

describe("toAttrRecord", () => {
  it("should convert basic entity attributes to object format", () => {
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

    const result = toAttrRecord(apiEntity);

    expect(result).toEqual({
      hostname: {
        type: AttrType.STRING,
        isMandatory: true,
        referral: [],
      },
    });
  });

  it("should convert entity with referral attributes (names only)", () => {
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

    const result = toAttrRecord(apiEntity);

    // Referral should contain only names, not full objects
    expect(result.location.referral).toEqual(["Datacenter", "Office"]);
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

    const result = toAttrRecord(apiEntity);

    expect(Object.keys(result)).toEqual(["name", "version", "port", "enabled"]);
    expect(result.name.type).toBe(AttrType.STRING);
    expect(result.version.type).toBe(AttrType.STRING);
    expect(result.port.type).toBe(AttrType.NUMBER);
    expect(result.enabled.type).toBe(AttrType.BOOLEAN);
  });

  it("should handle entity with no attributes", () => {
    const apiEntity = createEntityDetail({
      id: 3,
      name: "EmptyEntity",
      attrs: [],
    });

    const result = toAttrRecord(apiEntity);

    expect(result).toEqual({});
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

    const result = toAttrRecord(apiEntity);

    expect(result.someAttr.referral).toEqual([]);
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

    const result = toAttrRecord(apiEntity);

    expect(result.tags.type).toBe(AttrType.ARRAY_STRING);
    expect(result.servers.type).toBe(AttrType.ARRAY_OBJECT);
    expect(result.servers.referral).toEqual(["Server"]);
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

    const result = toAttrRecord(apiEntity);

    expect(result.required.isMandatory).toBe(true);
    expect(result.optional.isMandatory).toBe(false);
  });

  it("should create record keyed by attribute name for easy lookup", () => {
    const apiEntity = createEntityDetail({
      id: 8,
      name: "LookupTest",
      attrs: [
        createAttr({ id: 801, name: "hostname", type: AttrType.STRING }),
        createAttr({ id: 802, name: "ip_address", type: AttrType.STRING }),
      ],
    });

    const result = toAttrRecord(apiEntity);

    // Direct key access should work
    expect(result["hostname"]).toBeDefined();
    expect(result["ip_address"]).toBeDefined();
    expect(result["nonexistent"]).toBeUndefined();
  });
});
