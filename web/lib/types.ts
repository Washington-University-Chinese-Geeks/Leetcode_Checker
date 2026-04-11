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

export interface UserRecord {
  leetcode_username: string;
  display_name: string;
  server_region: "US" | "CN";
  last_updated: string;
  profile: UserProfile | null;
  totals: UserTotals | null;
  calendar: UserCalendar | null;
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
}

export interface Summary {
  generated_at: string;
  member_count: number;
  members: SummaryMember[];
}
