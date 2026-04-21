// Types mirror scripts/schemas/*.schema.json. Keep in sync when schemas change.

export interface Submission {
  id: string;
  title: string;
  title_slug: string;
  timestamp: string;
  proof_url?: string;
  submitted_at?: string;
}

export interface UserProfile {
  ranking: number | null;
  user_avatar: string | null;
  real_name: string | null;
  country_name: string | null;
  reputation: number | null;
}

export interface UserTotals {
  easy: number | null;
  medium: number | null;
  hard: number | null;
  all: number | null;
}

export interface UserCalendar {
  streak: number | null;
  total_active_days: number | null;
  submission_calendar: string | null;
}

export interface UserPlan {
  start_date: string;
  end_date: string | null;
  submissions_in_period: number;
}

export interface UserRecord {
  leetcode_username: string;
  display_name: string;
  server_region: "US" | "CN";
  last_updated: string;
  profile: UserProfile | null;
  totals: UserTotals | null;
  calendar: UserCalendar | null;
  plan: UserPlan | null;
  recent_submissions: Submission[];
}

export interface SummaryMember {
  leetcode_username: string;
  display_name: string;
  server_region: "US" | "CN";
  data_file: string;
  total_solved: number | null;
  recent_submission_count: number | null;
  last_submission_at: string | null;
  plan_start_date: string | null;
  plan_end_date: string | null;
  plan_submission_count: number | null;
}

export interface Summary {
  generated_at: string;
  member_count: number;
  members: SummaryMember[];
}

export type BenchmarkPeriod = "daily" | "weekly" | "monthly";

export interface BenchmarkEntry {
  leetcode_username: string;
  display_name: string;
  server_region: "US" | "CN";
  count: number;
}

export type Benchmarks = Record<BenchmarkPeriod, BenchmarkEntry[]>;
