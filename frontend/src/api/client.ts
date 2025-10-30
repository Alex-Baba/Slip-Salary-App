export interface LoginResponse {
  token: string;
  user_id: number;
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

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
