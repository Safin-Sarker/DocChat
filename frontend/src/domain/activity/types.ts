export interface AuditLogEntry {
  log_id: number;
  action: string;
  user_id: string | null;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, any> | null;
  ip_address: string | null;
  logged_at: string;
}
