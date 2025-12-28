/**
 * @jest-environment jsdom
 */

import { JobSerializers } from "@dmm-com/airone-apiclient-typescript-fetch";

import { JobOperations, JobStatuses } from "./Constants";
import {
  jobStatusLabel,
  jobOperationLabel,
  jobTargetLabel,
  getLatestCheckDate,
  updateLatestCheckDate,
  setCustomJobOperations,
} from "./JobUtil";

describe("JobUtil", () => {
  beforeEach(() => {
    localStorage.clear();
    // Reset custom job operations
    setCustomJobOperations([]);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe("jobStatusLabel", () => {
    test("should return '処理前' for PREPARING status", () => {
      expect(jobStatusLabel(JobStatuses.PREPARING)).toBe("処理前");
    });

    test("should return '完了' for DONE status", () => {
      expect(jobStatusLabel(JobStatuses.DONE)).toBe("完了");
    });

    test("should return '失敗' for ERROR status", () => {
      expect(jobStatusLabel(JobStatuses.ERROR)).toBe("失敗");
    });

    test("should return 'タイムアウト' for TIMEOUT status", () => {
      expect(jobStatusLabel(JobStatuses.TIMEOUT)).toBe("タイムアウト");
    });

    test("should return '処理中' for PROCESSING status", () => {
      expect(jobStatusLabel(JobStatuses.PROCESSING)).toBe("処理中");
    });

    test("should return 'キャンセル' for CANCELED status", () => {
      expect(jobStatusLabel(JobStatuses.CANCELED)).toBe("キャンセル");
    });

    test("should return '不明' for undefined status", () => {
      expect(jobStatusLabel(undefined)).toBe("不明");
    });

    test("should return '不明' for unknown status", () => {
      expect(jobStatusLabel(999)).toBe("不明");
    });
  });

  describe("jobOperationLabel", () => {
    test("should return '作成' for CREATE_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.CREATE_ENTRY)).toBe("作成");
    });

    test("should return '作成' for CREATE_ENTITY operation", () => {
      expect(jobOperationLabel(JobOperations.CREATE_ENTITY)).toBe("作成");
    });

    test("should return '編集' for EDIT_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.EDIT_ENTRY)).toBe("編集");
    });

    test("should return '編集' for EDIT_ENTITY operation", () => {
      expect(jobOperationLabel(JobOperations.EDIT_ENTITY)).toBe("編集");
    });

    test("should return '削除' for DELETE_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.DELETE_ENTRY)).toBe("削除");
    });

    test("should return '削除' for DELETE_ENTITY operation", () => {
      expect(jobOperationLabel(JobOperations.DELETE_ENTITY)).toBe("削除");
    });

    test("should return 'インポート' for IMPORT_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.IMPORT_ENTRY)).toBe("インポート");
    });

    test("should return 'エクスポート' for EXPORT_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.EXPORT_ENTRY)).toBe(
        "エクスポート",
      );
    });

    test("should return 'エクスポート' for EXPORT_SEARCH_RESULT operation", () => {
      expect(jobOperationLabel(JobOperations.EXPORT_SEARCH_RESULT)).toBe(
        "エクスポート",
      );
    });

    test("should return 'コピー' for COPY_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.COPY_ENTRY)).toBe("コピー");
    });

    test("should return 'コピー' for DO_COPY_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.DO_COPY_ENTRY)).toBe("コピー");
    });

    test("should return '復旧' for RESTORE_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.RESTORE_ENTRY)).toBe("復旧");
    });

    test("should return '一括更新' for BULK_EDIT_ENTRY operation", () => {
      expect(jobOperationLabel(JobOperations.BULK_EDIT_ENTRY)).toBe("一括更新");
    });

    test("should return '不明' for undefined operation", () => {
      expect(jobOperationLabel(undefined)).toBe("不明");
    });

    test("should return '不明' for unknown operation", () => {
      expect(jobOperationLabel(9999)).toBe("不明");
    });

    test("should return custom label for custom job operation", () => {
      setCustomJobOperations([{ operation: 100, label: "カスタム操作" }]);

      expect(jobOperationLabel(100)).toBe("カスタム操作");
    });

    test("should prioritize custom job operation over built-in", () => {
      setCustomJobOperations([
        { operation: JobOperations.CREATE_ENTRY, label: "カスタム作成" },
      ]);

      expect(jobOperationLabel(JobOperations.CREATE_ENTRY)).toBe(
        "カスタム作成",
      );
    });
  });

  describe("jobTargetLabel", () => {
    test("should format job label correctly", () => {
      const job = {
        id: 1,
        status: JobStatuses.DONE,
        operation: JobOperations.CREATE_ENTRY,
        target: { id: 1, name: "TestEntry", schemaId: 1, schemaName: "Entity" },
        createdAt: new Date(),
      } as JobSerializers;

      const result = jobTargetLabel(job);

      expect(result).toBe("[完了/作成] TestEntry");
    });

    test("should handle missing target name", () => {
      const job = {
        id: 1,
        status: JobStatuses.PROCESSING,
        operation: JobOperations.EDIT_ENTRY,
        target: { id: 1, name: "", schemaId: 1, schemaName: "Entity" },
        createdAt: new Date(),
      } as JobSerializers;

      const result = jobTargetLabel(job);

      expect(result).toBe("[処理中/編集] ");
    });

    test("should handle undefined target", () => {
      const job = {
        id: 1,
        status: JobStatuses.ERROR,
        operation: JobOperations.DELETE_ENTRY,
        target: undefined,
        createdAt: new Date(),
      } as unknown as JobSerializers;

      const result = jobTargetLabel(job);

      expect(result).toBe("[失敗/削除] ");
    });
  });

  describe("getLatestCheckDate", () => {
    test("should return null when no date is stored", () => {
      const result = getLatestCheckDate();

      expect(result).toBeNull();
    });

    test("should return Date object when valid date string is stored", () => {
      const dateString = "2024-01-15T12:00:00.000Z";
      localStorage.setItem("job__latest_check_date", dateString);

      const result = getLatestCheckDate();

      expect(result).toBeInstanceOf(Date);
      expect(result?.toISOString()).toBe(dateString);
    });
  });

  describe("updateLatestCheckDate", () => {
    test("should store date in localStorage", () => {
      const date = new Date("2024-01-15T12:00:00.000Z");

      updateLatestCheckDate(date);

      expect(localStorage.getItem("job__latest_check_date")).toBe(
        date.toISOString(),
      );
    });

    test("should update existing date", () => {
      const firstDate = new Date("2024-01-15T12:00:00.000Z");
      const secondDate = new Date("2024-01-16T12:00:00.000Z");

      updateLatestCheckDate(firstDate);
      updateLatestCheckDate(secondDate);

      expect(localStorage.getItem("job__latest_check_date")).toBe(
        secondDate.toISOString(),
      );
    });
  });
});
