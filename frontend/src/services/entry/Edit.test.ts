import { initializeEntryInfo } from "./Edit";
import { DjangoContext } from "services/DjangoContext";

test("initializeEntryInfo should return expect value", () => {
  global.window = Object.create({})
  //const djangoContext = DjangoContext.getInstance();
  const entity = {
    id: 1,
    name: "TestEntity",
    note: "hoge",
    status: 0,
    isToplevel: true,
    attrs: [{
      id: 2,
      index: 0,
      name: "attr",
      type: 1,
      isMandatory: true,
      isDeleteInChain: true,
    }],
    webhooks: [],
    isPublic: true,
  }
  expect(initializeEntryInfo(entity)).toBe({
    name: "",
    attrs: [

    ]
  })
})
