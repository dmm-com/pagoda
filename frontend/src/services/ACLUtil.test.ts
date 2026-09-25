import { ACLType, ACLTypeLabels, canEdit, canModifyACL } from "./ACLUtil";

import i18n from "i18n/config";

describe("ACLTypeLabels", () => {
  afterEach(async () => {
    await i18n.changeLanguage("ja");
  });

  test("should return Japanese labels by default", () => {
    expect(ACLTypeLabels[ACLType.Nothing]).toBe("権限なし");
    expect(ACLTypeLabels[ACLType.Readable]).toBe("閲覧");
    expect(ACLTypeLabels[ACLType.Writable]).toBe("閲覧・編集");
    expect(ACLTypeLabels[ACLType.Full]).toBe("閲覧・編集・削除");
  });

  test("should return English labels after changing language", async () => {
    await i18n.changeLanguage("en");

    expect(ACLTypeLabels[ACLType.Nothing]).toBe("No permission");
    expect(ACLTypeLabels[ACLType.Readable]).toBe("Read");
    expect(ACLTypeLabels[ACLType.Writable]).toBe("Read / Write");
    expect(ACLTypeLabels[ACLType.Full]).toBe("Read / Write / Delete");
  });
});

describe("canEdit", () => {
  test("should be false below Writable", () => {
    expect(canEdit(ACLType.Readable)).toBe(false);
  });

  test("should be true at Writable or above", () => {
    expect(canEdit(ACLType.Writable)).toBe(true);
    expect(canEdit(ACLType.Full)).toBe(true);
  });
});

describe("canModifyACL", () => {
  test("should be false below Full", () => {
    expect(canModifyACL(ACLType.Writable)).toBe(false);
  });

  test("should be true at Full", () => {
    expect(canModifyACL(ACLType.Full)).toBe(true);
  });
});
