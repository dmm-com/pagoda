import { NotificationMessages } from "./NotificationMessages";

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
});
