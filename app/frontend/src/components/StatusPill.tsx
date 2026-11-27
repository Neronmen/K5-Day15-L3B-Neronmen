import type { MyStatus } from "@/lib/types";
import { Pill } from "./ui";

export function MyStatusPill({ status }: { status: MyStatus }) {
  switch (status) {
    case "submitted":
      return <Pill tone="ok">Đã nộp</Pill>;
    case "late":
      return <Pill tone="warn">Nộp muộn</Pill>;
    case "overdue":
      return <Pill tone="bad">Quá hạn</Pill>;
    default:
      return <Pill tone="warn">Chưa nộp</Pill>;
  }
}
