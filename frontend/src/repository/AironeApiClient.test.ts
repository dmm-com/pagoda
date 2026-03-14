/**
 * @jest-environment jsdom
 */

import { fileDownload, getCsrfToken } from "./AironeApiClient";

describe("fileDownload", () => {
  const originalCreateObjectURL = URL.createObjectURL;
  const originalRevokeObjectURL = URL.revokeObjectURL;

  beforeEach(() => {
    URL.createObjectURL = jest
      .fn()
      .mockReturnValue("blob:http://localhost/fake-url");
    URL.revokeObjectURL = jest.fn();
  });

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
  });

  test("should create a Blob with the given data and trigger a download", () => {
    const clickMock = jest.fn();
    const createElementSpy = jest
      .spyOn(document, "createElement")
      .mockReturnValue({
        href: "",
        download: "",
        click: clickMock,
      } as unknown as HTMLAnchorElement);

    fileDownload("test data", "test.txt");

    // Verify Blob was created and passed to createObjectURL
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
    const blob = (URL.createObjectURL as jest.Mock).mock.calls[0][0] as Blob;
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.type).toBe("text/plain");

    // Verify anchor element was configured correctly
    const anchor = createElementSpy.mock.results[0].value;
    expect(anchor.href).toBe("blob:http://localhost/fake-url");
    expect(anchor.download).toBe("test.txt");

    // Verify click was called to trigger the download
    expect(clickMock).toHaveBeenCalledTimes(1);

    // Verify the object URL was revoked to free memory
    expect(URL.revokeObjectURL).toHaveBeenCalledWith(
      "blob:http://localhost/fake-url",
    );

    createElementSpy.mockRestore();
  });

  test("should handle empty data", () => {
    const clickMock = jest.fn();
    const createElementSpy = jest
      .spyOn(document, "createElement")
      .mockReturnValue({
        href: "",
        download: "",
        click: clickMock,
      } as unknown as HTMLAnchorElement);

    fileDownload("", "empty.txt");

    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
    const blob = (URL.createObjectURL as jest.Mock).mock.calls[0][0] as Blob;
    expect(blob.size).toBe(0);
    expect(clickMock).toHaveBeenCalledTimes(1);
    expect(URL.revokeObjectURL).toHaveBeenCalledTimes(1);

    createElementSpy.mockRestore();
  });

  test("should set correct filename on the anchor element", () => {
    const clickMock = jest.fn();
    const createElementSpy = jest
      .spyOn(document, "createElement")
      .mockReturnValue({
        href: "",
        download: "",
        click: clickMock,
      } as unknown as HTMLAnchorElement);

    fileDownload("yaml content", "export.yaml");

    const anchor = createElementSpy.mock.results[0].value;
    expect(anchor.download).toBe("export.yaml");

    createElementSpy.mockRestore();
  });
});

describe("getCsrfToken", () => {
  afterEach(() => {
    // Clear test cookies
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "sessionid=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "othercookie=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "lang=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  });

  test("should return csrf token from cookie", () => {
    document.cookie = "csrftoken=abc123";
    expect(getCsrfToken()).toBe("abc123");
  });

  test("should return empty string when no csrftoken cookie exists", () => {
    document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    document.cookie = "othercookie=value";
    expect(getCsrfToken()).toBe("");
  });

  test("should extract csrftoken when multiple cookies exist", () => {
    document.cookie = "sessionid=xyz789";
    document.cookie = "csrftoken=token456";
    document.cookie = "lang=en";
    expect(getCsrfToken()).toBe("token456");
  });

  test("should decode URI-encoded token values", () => {
    document.cookie = "csrftoken=" + encodeURIComponent("tok%en+special");
    expect(getCsrfToken()).toBe("tok%en+special");
  });
});
