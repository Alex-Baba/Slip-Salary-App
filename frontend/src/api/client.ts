export interface LoginResponse {
  token: string;
  user_id: number;
}

export interface MeResponse {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string | null;
  department: string | null;
  permissions: string[];
  subordinates?: { id: number; first_name: string; last_name: string; department?: string | null }[];
  subordinates_count?: number;
}

declare global {
  // Vite exposes import.meta.env; provide minimal typing.
  interface ImportMetaEnv {
    VITE_API_BASE?: string;
  }
  interface ImportMeta {
    env: ImportMetaEnv;
  }
}
const API_BASE: string = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8000';

async function safeFetch(url: string, opts: RequestInit = {}) {
  try {
    return await fetch(url, opts);
  } catch (err: any) {
    // More descriptive network error
    throw new Error(`Network error contacting ${url}: ${err.message || err}`);
  }
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const payload = await res.json().catch(() => ({}));
    const msg = payload?.model_errors ? JSON.stringify(payload.model_errors) : 'Login failed';
    throw new Error(msg);
  }
  return res.json();
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchMe(): Promise<MeResponse> {
  const headers: Record<string,string> = { 'Content-Type': 'application/json', ...authHeaders() };
  const res = await fetch(`${API_BASE}/api/auth/me/`, { headers });
  if (!res.ok) {
    throw new Error('Failed to load profile');
  }
  return res.json();
}

// Endpoint helpers (POST for actions) - all wrapped with auth & simple status handling.
async function postEndpoint(path: string, body: any): Promise<any> {
  const headers: Record<string,string> = {
    'Content-Type': 'application/json',
    'Idempotency-Key': body?.idempotencyKey || crypto.randomUUID(),
    ...authHeaders()
  };
  let res: Response;
  try {
    res = await safeFetch(`${API_BASE}${path}`, { method: 'POST', headers, body: JSON.stringify(body) });
  } catch (err) {
    throw err;
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.error || data.model_errors ? JSON.stringify(data.model_errors || data.error) : `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

export async function sendPayslip(employeeId: number) {
  return postEndpoint('/api/employees/send_payslip_email/', { employee_id: employeeId });
}

export async function sendAggregatedCsv(employeeId: number, year: number, month: number) {
  return postEndpoint('/api/employees/send_aggregated_csv_email/', { employee_id: employeeId, year, month });
}

export async function sendManagerAggregatedCsv(managerId: number, year: number, month: number) {
  return postEndpoint('/api/employees/send_manager_aggregated_csv_email/', { manager_id: managerId, year, month });
}

export interface BonusCreatePayload {
  employee_id: number;
  amount: number;
  description: string;
  date?: string; // ISO optional
}

export async function createBonus(payload: BonusCreatePayload) {
  return postEndpoint('/api/bonuses/create/', payload);
}

export async function listBonuses(employeeId?: number) {
  const query = employeeId ? `?employee_id=${employeeId}` : '';
  const headers: Record<string,string> = { ...authHeaders() };
  const res = await fetch(`${API_BASE}/api/bonuses/list/${query}`, { headers });
  if (!res.ok) {
    throw new Error('Failed to load bonuses');
  }
  return res.json();
}

export interface EmployeeCreatePayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  cnp: string;
  role_id: number;
  manager_id?: number | null;
  department_id?: number | null;
  base_salary?: number;
  expected_working_days?: number;
}

export async function createEmployee(payload: EmployeeCreatePayload) {
  const headers: Record<string,string> = { 'Content-Type': 'application/json', ...authHeaders() };
  const res = await fetch(`${API_BASE}/api/employees/`, { method: 'POST', headers, body: JSON.stringify(payload) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to create employee';
    throw new Error(msg);
  }
  return data;
}

// Listing & auxiliary endpoints for admin dashboard
export async function listRoles() {
  const url = `${API_BASE}/api/roles/`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to load roles (${res.status})`);
  return res.json();
}

export async function listDepartments() {
  const url = `${API_BASE}/api/departments/list/`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to load departments (${res.status})`);
  return res.json();
}

export async function createDepartment(name: string) {
  const res = await fetch(`${API_BASE}/api/departments/create/`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() }, body: JSON.stringify({ name })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to create department');
  return data;
}

export async function updateDepartment(departmentId: number, name: string) {
  const headers: Record<string,string> = { 'Content-Type': 'application/json', ...authHeaders() };
  const res = await fetch(`${API_BASE}/api/departments/${departmentId}/update/`, { method: 'PATCH', headers, body: JSON.stringify({ name }) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to update department');
  return data;
}

export async function deleteDepartment(departmentId: number) {
  const res = await fetch(`${API_BASE}/api/departments/${departmentId}/delete/`, { method: 'DELETE', headers: authHeaders() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to delete department');
  return data;
}

export async function listManagers() {
  const url = `${API_BASE}/api/managers/`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to load managers (${res.status})`);
  return res.json();
}

export async function listDepartmentEmployees() {
  const url = `${API_BASE}/api/departments/my_employees/`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to load department employees (${res.status})`);
  return res.json();
}

export async function generateEmployeePdf(employeeId: number) {
  const headers: Record<string,string> = { ...authHeaders(), 'Idempotency-Key': crypto.randomUUID() };
  const res = await fetch(`${API_BASE}/api/employees/${employeeId}/generate_pdf/`, { method: 'POST', headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to generate PDF');
  return data;
}

export async function sendEmployeePayslip(employeeId: number) {
  const headers: Record<string,string> = { ...authHeaders(), 'Idempotency-Key': crypto.randomUUID() };
  const res = await fetch(`${API_BASE}/api/employees/${employeeId}/send_payslip/`, { method: 'POST', headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to send payslip');
  return data;
}

export async function listDepartmentManagers(departmentId: number) {
  const url = `${API_BASE}/api/departments/${departmentId}/managers/`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to load department managers (${res.status})`);
  return res.json();
}

// Aggregated CSV generation/status helpers
export async function generateEmployeeAggregate(employeeId: number, year?: number, month?: number) {
  const body: any = {};
  if (year) body.year = year;
  if (month) body.month = month;
  const headers: Record<string,string> = { 'Content-Type': 'application/json', ...authHeaders(), 'Idempotency-Key': crypto.randomUUID() };
  const res = await fetch(`${API_BASE}/api/employees/${employeeId}/generate_aggregate/`, { method: 'POST', headers, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to generate aggregate CSV');
  return data;
}

export async function getEmployeeAggregateStatus(employeeId: number, year?: number, month?: number) {
  const q = year ? `?year=${year}${month ? `&month=${month}` : ''}` : (month ? `?month=${month}` : '');
  const res = await safeFetch(`${API_BASE}/api/employees/${employeeId}/aggregate_status/${q}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch aggregate status (${res.status})`);
  return res.json();
}

export async function generateManagerTeamAggregate(managerId: number, year?: number, month?: number) {
  const body: any = {};
  if (year) body.year = year;
  if (month) body.month = month;
  const headers: Record<string,string> = { 'Content-Type': 'application/json', ...authHeaders(), 'Idempotency-Key': crypto.randomUUID() };
  const res = await fetch(`${API_BASE}/api/managers/${managerId}/generate_team_aggregate/`, { method: 'POST', headers, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to generate manager aggregate CSV');
  return data;
}

export async function getManagerAggregateStatus(managerId: number, year?: number, month?: number) {
  const q = year ? `?year=${year}${month ? `&month=${month}` : ''}` : (month ? `?month=${month}` : '');
  const res = await safeFetch(`${API_BASE}/api/managers/${managerId}/aggregate_status/${q}`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch manager aggregate status (${res.status})`);
  return res.json();
}

export async function listAttendance(year: number, month: number) {
  const url = `${API_BASE}/api/attendance/?year=${year}&month=${month}`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to load attendance (${res.status})`);
  return res.json();
}

export async function listAllEmployees() {
  const url = `${API_BASE}/api/employees_all/`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to load employees (${res.status})`);
  return res.json();
}

export async function updateAttendance(employeeId: number, working_days: number, leave_days: number, year: number, month: number) {
  return postEndpoint('/api/attendance/upsert/', { employee_id: employeeId, working_days, leave_days, year, month });
}

export async function patchAttendance(attendanceId: number, patch: { working_days?: number; leave_days?: number }) {
  const headers: Record<string,string> = { 'Content-Type': 'application/json', ...authHeaders() };
  const res = await fetch(`${API_BASE}/api/attendance/${attendanceId}/update/`, { method: 'PATCH', headers, body: JSON.stringify(patch) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to update attendance');
  return data;
}

export async function deleteEmployee(employeeId: number) {
  const res = await fetch(`${API_BASE}/api/employees/${employeeId}/delete/`, { method: 'DELETE', headers: authHeaders() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to delete employee');
  return data;
}

export async function aggregateEmployee(employeeId: number, year: number, month: number) {
  const res = await fetch(`${API_BASE}/api/employees/aggregate_data/?employee_id=${employeeId}&year=${year}&month=${month}`, { headers: authHeaders() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.model_errors ? JSON.stringify(data.model_errors) : 'Failed to load aggregate');
  return data;
}

export async function downloadEmployeePdf(employeeId: number): Promise<Blob> {
  const url = `${API_BASE}/api/employees/create_pdf/?employee_id=${employeeId}`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch PDF (${res.status})`);
  return res.blob();
}

export async function pingHealth() {
  const url = `${API_BASE}/api/health/`;
  const res = await safeFetch(url);
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json().catch(() => ({}));
}
