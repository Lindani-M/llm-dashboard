export interface KPIs {
  total_customers: number;
  churned_customers: number;
  retained_customers: number;
  churn_rate: number;
  retention_rate: number;
  avg_balance_churned: number;
  avg_balance_retained: number;
}

export interface SegmentStat {
  total: number;
  churned: number;
  retained?: number;
  churn_rate: number;
}

export interface Metrics {
  kpis: KPIs;
  geography: Record<string, SegmentStat>;
  age: Record<string, SegmentStat>;
  gender: Record<string, SegmentStat>;
  products: Record<string, SegmentStat>;
  activity: Record<string, SegmentStat>;
  balance: Record<string, SegmentStat>;
  credit_score: Record<string, SegmentStat>;
  tenure: Record<string, SegmentStat>;
}

export interface CommentarySection {
  ai_generated_content: string;
  user_overridden_content: string | null;
  is_user_override_active: boolean;
  last_data_refresh: string;
  last_override_at: string | null;
  active_content: string;
}

export type Commentary = Record<string, CommentarySection>;
