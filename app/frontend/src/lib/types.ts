// Khớp với backend/app/schemas.py

export type Role = "teacher" | "student";
export type AIMode = "strict" | "extended";

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ClassOut {
  id: string;
  name: string;
  subject: string;
  ai_mode: AIMode;
  class_code: string;
}

export interface ClassSummary extends ClassOut {
  students: number;
  documents: number;
  open_assignments: number;
  pending_grades: number;
  next_session_at: string | null;
  schedule_text: string;
}

export interface Member {
  id: string;
  email: string;
  name: string;
  activated: boolean;
}

export interface DocumentOut {
  id: string;
  file_name: string;
  status: "processing" | "ready" | "failed";
  uploaded_at: string | null;
  page_count: number | null;
  error: string | null;
  is_pdf: boolean;
}

export interface Assignment {
  id: string;
  class_id: string;
  title: string;
  prompt: string;
  rubric: string | null;
  due_at: string;
  allow_late: boolean;
  version: number;
  reference_answer?: string | null;
  attachment_name: string | null;
}

export interface ClassDetail {
  cls: ClassOut;
  members: Member[];
  documents: DocumentOut[];
  assignments: Assignment[];
  sessions: ClassSession[];
  announcements: Announcement[];
}

export interface AddStudentsOut {
  added: string[];
  already_in_class: string[];
  invalid: string[];
}

export interface Submission {
  id: string;
  assignment_version: number;
  content: string | null;
  has_image: boolean;
  locked: boolean;
  submitted_at: string | null;
  is_late: boolean;
}

export interface SubmissionRow {
  student_id: string;
  name: string;
  email: string;
  status: "submitted" | "late" | "missing";
  submitted_at: string | null;
  submission_id: string | null;
  grade_status: "pending_review" | "published" | null;
  score: number | null;
  ai_status: GradeDetail["ai_status"];
  ai_score: number | null;
}

export type MyStatus = "missing" | "submitted" | "late" | "overdue";

export interface StudentAssignment extends Assignment {
  class_name: string;
  my_status: MyStatus;
}

export interface StudentClass extends ClassOut {
  teacher_name: string;
  next_session_at: string | null;
  schedule_text: string;
}

export interface StudentHome {
  classes: StudentClass[];
  upcoming: StudentAssignment[];
  announcements: Announcement[];
}

export interface StudentClassView {
  cls: ClassOut;
  documents: DocumentOut[];
  assignments: StudentAssignment[];
  sessions: ClassSession[];
  announcements: Announcement[];
}

export interface StudentAssignmentDetail {
  assignment: Assignment;
  submission: Submission | null;
  can_submit: boolean;
}

export interface Result {
  published: boolean;
  score?: number | null;
  feedback?: string | null;
  breakdown?: string | null;
  submission?: Submission | null;
}

// ---------- Giai đoạn 2–3 ----------
export interface Citation {
  label: string;
  document_id: string;
  page_number: number;
  /** Có khi nguồn là trang web tìm trên Google */
  url?: string;
  title?: string;
}

export interface WebSource {
  label: string;
  title: string;
  url: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  mode: "lecture" | "hint" | "answer";
  content: string;
  citations: Citation[];
  created_at: string | null;
}

export interface ChatLog extends ChatMessage {
  student_id: string;
  student_name: string;
  flagged: "jailbreak" | "impersonation" | "ask_answer" | null;
  assignment_id: string | null;
  document_id: string | null;
  context: string;
}

export interface StudentDocument {
  id: string;
  class_id: string;
  class_name: string;
  ai_mode: AIMode;
  file_name: string;
  page_count: number | null;
  is_pdf: boolean;
  unit: string;
}

export interface DocPage {
  page_number: number;
  text: string;
}

export interface RubricItem {
  criterion: string;
  max_points: number;
  points: number;
  reason: string;
}

export interface AIBreakdown {
  ocr_text: string | null;
  image_confidence: number | null;
  steps: { question: string; content: string }[];
  checks: { question: string; step: string; verdict: "correct" | "partial" | "wrong" | "missing"; explanation: string }[];
  items: RubricItem[];
  summary: string;
  feedback: string;
}

export interface GradeDetail {
  submission_id: string;
  status: "pending_review" | "published";
  ai_status: "queued" | "running" | "done" | "manual" | "failed" | null;
  ai_score: number | null;
  ai_breakdown: AIBreakdown | null;
  ai_error: string | null;
  score: number | null;
  feedback: string | null;
  breakdown: RubricItem[] | null;
}

export interface NotificationItem {
  id: string;
  kind: "doc_ready" | "doc_failed" | string;
  payload: Record<string, unknown>;
  read: boolean;
  created_at: string | null;
}

// ---------- Lịch học & thông báo ----------
export interface ClassSession {
  id: string;
  weekday: number; // 0 = Thứ 2 … 6 = Chủ nhật
  start_time: string;
  end_time: string;
  room: string | null;
}

export type AnnouncementKind = "general" | "cancel" | "makeup";

export interface Announcement {
  id: string;
  class_id: string;
  class_name: string;
  kind: AnnouncementKind;
  title: string;
  body: string;
  event_date: string | null;
  event_start: string | null;
  event_end: string | null;
  session_id: string | null;
  pinned: boolean;
  created_at: string | null;
}

export interface CalendarItem {
  date: string;
  start_time: string;
  end_time: string;
  class_id: string;
  class_name: string;
  subject: string;
  room: string | null;
  kind: "regular" | "makeup";
  session_id: string | null;
  cancelled: boolean;
  note: string | null;
}

// ---------- Trợ lý AI giáo viên ----------
export type AssistantTask = "ask" | "summary" | "outline" | "quiz" | "lesson";

export interface SourceDoc {
  id: string;
  file_name: string;
  page_count: number | null;
  is_pdf: boolean;
  unit: string;
}

export interface SourceClass {
  id: string;
  name: string;
  subject: string;
  documents: SourceDoc[];
}

export interface SearchHit {
  class_id: string;
  class_name: string;
  document_id: string;
  file_name: string;
  page_number: number;
  source_label: string;
  snippet: string;
}
