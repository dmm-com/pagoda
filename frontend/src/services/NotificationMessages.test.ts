import { NotificationMessages } from "./NotificationMessages";

import i18n from "i18n/config";

describe("NotificationMessages", () => {
  describe("jobRegistered", () => {
    test("should include operation name", () => {
      expect(NotificationMessages.jobRegistered("エクスポート")).toBe(
        "エクスポートのジョブ登録に成功しました",
      );
    });
  });

  describe("jobRegistrationFailed", () => {
    test("should include operation name", () => {
      expect(NotificationMessages.jobRegistrationFailed("コピー")).toBe(
        "コピーのジョブ登録に失敗しました",
      );
    });
  });

  describe("jobCompleted", () => {
    test("should include label", () => {
      expect(NotificationMessages.jobCompleted("テストジョブ")).toBe(
        "テストジョブが完了しました",
      );
    });
  });

  describe("jobFailed", () => {
    test("should include label", () => {
      expect(NotificationMessages.jobFailed("テストジョブ")).toBe(
        "テストジョブが失敗しました",
      );
    });
  });

  describe("jobTimedOut", () => {
    test("should include label", () => {
      expect(NotificationMessages.jobTimedOut("テストジョブ")).toBe(
        "テストジョブがタイムアウトしました",
      );
    });
  });

  describe("operationCompleted", () => {
    test("should include target and operation names", () => {
      expect(NotificationMessages.operationCompleted("アイテム", "作成")).toBe(
        "アイテムの作成が完了しました。",
      );
    });
  });

  describe("operationFailed", () => {
    test("should include target and operation names", () => {
      expect(NotificationMessages.operationFailed("アイテム", "更新")).toBe(
        "アイテムの更新が失敗しました。",
      );
    });
  });

  describe("exportReady", () => {
    test("should include target name", () => {
      expect(NotificationMessages.exportReady("テストエンティティ")).toBe(
        "テストエンティティのエクスポートが完了しました",
      );
    });
  });

  describe("uploadFailed", () => {
    test("should show base message without detail", () => {
      expect(NotificationMessages.uploadFailed()).toBe(
        "ファイルのアップロードに失敗しました",
      );
    });

    test("should include detail when provided", () => {
      expect(NotificationMessages.uploadFailed("サイズ超過")).toBe(
        "ファイルのアップロードに失敗しました: サイズ超過",
      );
    });
  });

  describe("English messages", () => {
    afterEach(async () => {
      await i18n.changeLanguage("ja");
    });

    test("jobCompleted should include label in English", async () => {
      await i18n.changeLanguage("en");

      expect(NotificationMessages.jobCompleted("Test job")).toBe(
        "Test job completed",
      );
    });

    test("operationCompleted should include target and operation names in English", async () => {
      await i18n.changeLanguage("en");

      expect(NotificationMessages.operationCompleted("Entry", "Create")).toBe(
        "Create Entry completed.",
      );
    });

    test("uploadFailed should show English message with detail", async () => {
      await i18n.changeLanguage("en");

      expect(NotificationMessages.uploadFailed()).toBe(
        "Failed to upload the file",
      );
      expect(NotificationMessages.uploadFailed("too large")).toBe(
        "Failed to upload the file: too large",
      );
    });
  });
});
