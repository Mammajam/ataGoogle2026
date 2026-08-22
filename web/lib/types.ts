export type InventoryLine = {
  id: string;
  scope: number;
  category: number | null;
  activity: string;
  activity_key: string;
  quantity: number;
  unit: string;
  tco2e: number;
  method: string;
  factor_id: string;
  factor_source: string;
  confidence: number;
  source: string;
  source_thumb: string;
  gap_flag: string | null;
  assumption: string | null;
  memory_applied?: boolean;
};

export type AuditEvent = {
  step: string;
  message: string;
};

export type A2uiMessage = Record<string, unknown>;

export type ExtractionWidget = {
  kind: string;
  line_id: string;
  run_id?: string;
  recommended: { quantity: number; unit: string; label?: string };
  alternate: { quantity: number; unit: string; label?: string };
  recommended_tco2e: number;
  alternate_tco2e: number;
};

export type Draft = {
  run_id: string;
  company_id: string;
  company_name: string;
  reporting_year: number;
  status: string;
  lines: InventoryLine[];
  totals: {
    scope1_tco2e: number;
    scope2_tco2e: number;
    scope3_tco2e: number;
    total_tco2e: number;
  };
  artifacts: string[];
  policy_applied: boolean;
  policy_keys: string[];
  widget: ExtractionWidget | null;
  a2ui: A2uiMessage[];
  events: AuditEvent[];
  last_confirmation?: { line_id: string; quantity: number; unit: string };
};

export type MemoryResponse = {
  company_id: string;
  overrides: Array<Record<string, unknown>>;
  policy_applied: boolean;
};

export type ConfirmPayload = {
  run_id: string;
  line_id: string;
  quantity: number;
  unit: string;
  company_id?: string;
};
