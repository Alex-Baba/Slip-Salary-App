import React, { useEffect, useState } from 'react';
import { fetchMe, sendPayslip, sendAggregatedCsv, sendManagerAggregatedCsv, createBonus, listBonuses, createEmployee, listRoles, listDepartments, createDepartment as apiCreateDepartment, listManagers, listDepartmentManagers, listAttendance, updateAttendance as apiUpdateAttendance, deleteEmployee as apiDeleteEmployee, aggregateEmployee, downloadEmployeePdf, listAllEmployees, pingHealth } from '../api/client';

interface BonusFormState {
  employee_id: string;
  amount: string;
  description: string;
  date: string;
}

const Dashboard: React.FC = () => {
  const [me, setMe] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bonusForm, setBonusForm] = useState<BonusFormState>({ employee_id: '', amount: '', description: '', date: '' });
  const [bonusSubmitting, setBonusSubmitting] = useState(false);
  const [bonuses, setBonuses] = useState<any[]>([]);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  // Employee creation form (admin)
  const [empForm, setEmpForm] = useState({
    email: '', password: '', first_name: '', last_name: '', cnp: '', role_id: '', manager_id: '', department_id: '', base_salary: '', expected_working_days: ''
  });
  const [empSubmitting, setEmpSubmitting] = useState(false);
  // Admin controls state
  const [targetEmployeeId, setTargetEmployeeId] = useState<string>('');
  const [targetManagerId, setTargetManagerId] = useState<string>('');
  const [periodYear, setPeriodYear] = useState<string>(String(new Date().getFullYear()));
  const [periodMonth, setPeriodMonth] = useState<string>(String(new Date().getMonth() + 1));
  // Data viewing (admin) simple results
  const [rolesData, setRolesData] = useState<any[]>([]);
  const [departmentsData, setDepartmentsData] = useState<any[]>([]);
  const [managersData, setManagersData] = useState<any[]>([]);
  const [attendanceData, setAttendanceData] = useState<any[]>([]);
  const [attendanceWorking, setAttendanceWorking] = useState<string>('');
  const [attendanceLeave, setAttendanceLeave] = useState<string>('');
  const [aggregateData, setAggregateData] = useState<any | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [deptManagersDeptId, setDeptManagersDeptId] = useState('');
  const [departmentCreateName, setDepartmentCreateName] = useState('');
  const [employeesData, setEmployeesData] = useState<any[]>([]);
  const [pingResult, setPingResult] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const profile = await fetchMe();
        setMe(profile);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const isEmployee = me?.permissions?.includes('employee');
  const isManager = me?.permissions?.includes('manager');
  const isAdmin = me?.permissions?.includes('admin');

  async function handleSendPayslip(employeeIdOverride?: number) {
    if (!me) return;
    setActionMsg(null);
    const id = employeeIdOverride || me.id;
    try {
      await sendPayslip(id);
      setActionMsg(`Payslip email sent for employee ${id}.`);
    } catch (e: any) {
      setActionMsg(`Error: ${e.message}`);
    }
  }

  async function handleSendAggregatedCsv(employeeIdOverride?: number) {
    if (!me) return;
    setActionMsg(null);
    const year = Number(periodYear);
    const month = Number(periodMonth);
    const id = employeeIdOverride || me.id;
    try {
      await sendAggregatedCsv(id, year, month);
      setActionMsg(`Aggregated CSV email sent for employee ${id} (${year}-${month}).`);
    } catch (e: any) {
      setActionMsg(`Error: ${e.message}`);
    }
  }

  async function handleSendManagerCsv(managerIdOverride?: number) {
    if (!me) return;
    setActionMsg(null);
    const year = Number(periodYear);
    const month = Number(periodMonth);
    const mid = managerIdOverride || me.id;
    try {
      await sendManagerAggregatedCsv(mid, year, month);
      setActionMsg(`Team aggregated CSV email sent for manager ${mid} (${year}-${month}).`);
    } catch (e: any) {
      setActionMsg(`Error: ${e.message}`);
    }
  }

  function updateBonusField<K extends keyof BonusFormState>(field: K, value: string) {
    setBonusForm(prev => ({ ...prev, [field]: value }));
  }

  async function submitBonus(e: React.FormEvent) {
    e.preventDefault();
    setBonusSubmitting(true);
    setActionMsg(null);
    try {
      const payload = {
        employee_id: Number(bonusForm.employee_id),
        amount: Number(bonusForm.amount),
        description: bonusForm.description,
        date: bonusForm.date || undefined
      };
      await createBonus(payload);
      setActionMsg('Bonus created.');
      setBonusForm({ employee_id: '', amount: '', description: '', date: '' });
    } catch (e: any) {
      setActionMsg(`Error: ${e.message}`);
    } finally {
      setBonusSubmitting(false);
    }
  }

  async function refreshBonuses() {
    setActionMsg(null);
    try {
      const data = await listBonuses();
      setBonuses(data);
      setActionMsg(`Loaded ${data.length} bonuses.`);
    } catch (e: any) {
      setActionMsg(`Error: ${e.message}`);
    }
  }

  function updateEmpField(field: string, value: string) {
    setEmpForm(prev => ({ ...prev, [field]: value }));
  }

  async function submitEmployee(e: React.FormEvent) {
    e.preventDefault();
    setEmpSubmitting(true);
    setActionMsg(null);
    try {
      const payload: any = {
        email: empForm.email,
        password: empForm.password,
        first_name: empForm.first_name,
        last_name: empForm.last_name,
        cnp: empForm.cnp,
        role_id: Number(empForm.role_id),
      };
      if (empForm.manager_id) payload.manager_id = Number(empForm.manager_id);
      if (empForm.department_id) payload.department_id = Number(empForm.department_id);
      if (empForm.base_salary) payload.base_salary = Number(empForm.base_salary);
      if (empForm.expected_working_days) payload.expected_working_days = Number(empForm.expected_working_days);
      await createEmployee(payload);
      setActionMsg('Employee created.');
      setEmpForm({ email: '', password: '', first_name: '', last_name: '', cnp: '', role_id: '', manager_id: '', department_id: '', base_salary: '', expected_working_days: '' });
    } catch (e: any) {
      setActionMsg(`Error: ${e.message}`);
    } finally {
      setEmpSubmitting(false);
    }
  }

  // Lightweight auth header helper (mirror client.ts logic) for direct fetch calls
  function authHeaders(): Record<string,string> {
    const token = localStorage.getItem('auth_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Admin fetch helpers
  async function fetchRoles() { try { const data = await listRoles(); setRolesData(data); setActionMsg('Roles loaded'); } catch { setActionMsg('Error loading roles'); } }
  async function fetchDepartments() { try { const data = await listDepartments(); setDepartmentsData(data); setActionMsg('Departments loaded'); } catch { setActionMsg('Error loading departments'); } }
  async function createDepartment() { if (!departmentCreateName) return; try { await apiCreateDepartment(departmentCreateName); setDepartmentCreateName(''); fetchDepartments(); setActionMsg('Department created'); } catch { setActionMsg('Error creating department'); } }
  async function fetchManagers() { try { const data = await listManagers(); setManagersData(data); setActionMsg('Managers loaded'); } catch { setActionMsg('Error loading managers'); } }
  async function fetchAllEmployees() { try { const data = await listAllEmployees(); setEmployeesData(data); setActionMsg(`Loaded ${data.length} employees`); } catch (e:any) { setActionMsg(`Error: ${e.message}`); } }
  async function pingApi() { setActionMsg(null); setPingResult(null); try { const data = await pingHealth(); setPingResult(JSON.stringify(data)); setActionMsg('API reachable'); } catch (e:any) { setActionMsg(`Error: ${e.message}`); setPingResult(null); } }
  async function fetchDepartmentManagers() { if (!deptManagersDeptId) return; try { const data = await listDepartmentManagers(Number(deptManagersDeptId)); setManagersData(data); setActionMsg('Dept managers loaded'); } catch { setActionMsg('Error loading dept managers'); } }
  async function fetchAttendance() { const year = Number(periodYear); const month = Number(periodMonth); try { const data = await listAttendance(year, month); setAttendanceData(data); setActionMsg('Attendance loaded'); } catch { setActionMsg('Error loading attendance'); } }
  async function updateAttendance() {
    if (!targetEmployeeId) return;
    const year = Number(periodYear);
    const month = Number(periodMonth);
    // Prefer explicit inputs; if empty, fall back to a loaded attendance record for that employee/period, otherwise 0.
    const explicitWd = attendanceWorking !== '' ? Number(attendanceWorking) : undefined;
    const explicitLd = attendanceLeave !== '' ? Number(attendanceLeave) : undefined;
    const existing = attendanceData.find(r => r.employee_id === Number(targetEmployeeId));
    const wd = explicitWd !== undefined ? explicitWd : (existing ? existing.working_days : 0);
    const ld = explicitLd !== undefined ? explicitLd : (existing ? existing.leave_days : 0);
    try {
      const data = await apiUpdateAttendance(Number(targetEmployeeId), wd, ld, year, month);
      setActionMsg(`Attendance updated id ${data.id}`);
      fetchAttendance();
    } catch {
      setActionMsg('Error updating attendance');
    }
  }
  // Note: the previous bulk +1 helper was removed per request
  async function deleteEmployee() { if (!targetEmployeeId) return; try { await apiDeleteEmployee(Number(targetEmployeeId)); setActionMsg('Employee deleted'); } catch { setActionMsg('Error deleting employee'); } }
  async function fetchAggregate() { if (!targetEmployeeId) return; const year = Number(periodYear); const month = Number(periodMonth); try { const data = await aggregateEmployee(Number(targetEmployeeId), year, month); setAggregateData(data); setActionMsg('Aggregate loaded'); } catch { setActionMsg('Error loading aggregate'); } }
  async function downloadPdf() { if (!targetEmployeeId) return; setPdfLoading(true); try { const blob = await downloadEmployeePdf(Number(targetEmployeeId)); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `employee_${targetEmployeeId}_report.pdf`; a.click(); URL.revokeObjectURL(url); setActionMsg('PDF downloaded'); } catch { setActionMsg('Error downloading PDF'); } finally { setPdfLoading(false); } }

  if (loading) return <div style={{ padding: '2rem' }}>Loading...</div>;
  if (error) return <div style={{ padding: '2rem', color: 'red' }}>{error}</div>;

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: 900, margin: '0 auto' }}>
      <h2>Dashboard</h2>
      <p>Welcome {me.first_name} {me.last_name} ({me.role || 'no-role'})</p>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        {/* Base employee actions */}
        {isEmployee && (
          <>
            <button onClick={() => handleSendPayslip()} style={btnStyle}>Send My Payslip</button>
            <button onClick={() => handleSendAggregatedCsv()} style={btnStyle}>Send My Aggregated CSV</button>
          </>
        )}
        {/* Manager/Admin actions */}
        {(isManager || isAdmin) && (
          <>
            <button onClick={() => handleSendManagerCsv()} style={btnStyle}>Send My Team Aggregated CSV</button>
            <button onClick={refreshBonuses} style={btnStyle}>Load Bonuses (Dept/All)</button>
          </>
        )}
      </div>
      {/* Admin extended controls */}
      {isAdmin && (
        <div style={{ border: '1px solid #444', padding: '1rem', marginBottom: '1.5rem', background: '#0f172a', color: '#e2e8f0', borderRadius: 6 }}>
          <h3 style={{ marginTop: 0 }}>Admin Controls</h3>
          <div style={{ display: 'grid', gap: '0.75rem', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))' }}>
            <label style={adminLabelStyle}>Employee ID
              <input value={targetEmployeeId} onChange={e => setTargetEmployeeId(e.target.value)} placeholder="Target employee" style={adminInputStyle} />
            </label>
            <label style={adminLabelStyle}>Manager ID
              <input value={targetManagerId} onChange={e => setTargetManagerId(e.target.value)} placeholder="Target manager" style={adminInputStyle} />
            </label>
            <label style={adminLabelStyle}>Year
              <input value={periodYear} onChange={e => setPeriodYear(e.target.value)} style={adminInputStyle} />
            </label>
            <label style={adminLabelStyle}>Month
              <input value={periodMonth} onChange={e => setPeriodMonth(e.target.value)} style={adminInputStyle} />
            </label>
          </div>
          {/* Grouped sections */}
          <div style={{ display: 'grid', gap: '1.25rem', marginTop: '1rem' }}>
            <section style={adminSectionStyle}>
              <h4 style={sectionTitleStyle}>Payroll Emails & Reports</h4>
              <div style={sectionGridStyle}>                
                <button style={btnAdminAction} disabled={!targetEmployeeId} onClick={() => targetEmployeeId && handleSendPayslip(Number(targetEmployeeId))}>Send Payslip</button>
                <button style={btnAdminAction} disabled={!targetEmployeeId} onClick={() => targetEmployeeId && handleSendAggregatedCsv(Number(targetEmployeeId))}>Send Aggregated CSV</button>
                <button style={btnAdminAction} disabled={!targetManagerId} onClick={() => targetManagerId && handleSendManagerCsv(Number(targetManagerId))}>Send Team CSV</button>
                <button style={btnAdminAction} disabled={!targetEmployeeId || pdfLoading} onClick={downloadPdf}>{pdfLoading ? 'Downloading…' : 'Download Payslip PDF'}</button>
                <button style={btnAdminAction} disabled={!targetEmployeeId} onClick={fetchAggregate}>Load Aggregate Data</button>
                <button style={btnAdminAction} onClick={pingApi}>Ping API</button>
              </div>
            </section>
            <section style={adminSectionStyle}>
              <h4 style={sectionTitleStyle}>Directory & Structure</h4>
              <div style={sectionGridStyle}>
                <button style={btnAdminAction} onClick={fetchRoles}>List Roles</button>
                <button style={btnAdminAction} onClick={fetchDepartments}>List Departments</button>
                <button style={btnAdminAction} onClick={fetchAllEmployees}>List All Employees</button>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <input placeholder="New Dept Name" value={departmentCreateName} onChange={e => setDepartmentCreateName(e.target.value)} style={adminInputStyle} />
                  <button style={btnAdminAction} disabled={!departmentCreateName} onClick={createDepartment}>Create Dept</button>
                </div>
                <button style={btnAdminAction} onClick={fetchManagers}>List Managers</button>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <input placeholder="Dept ID" value={deptManagersDeptId} onChange={e => setDeptManagersDeptId(e.target.value)} style={adminInputStyle} />
                  <button style={btnAdminAction} disabled={!deptManagersDeptId} onClick={fetchDepartmentManagers}>Dept Managers</button>
                </div>
              </div>
            </section>
            <section style={adminSectionStyle}>
              <h4 style={sectionTitleStyle}>Attendance Management</h4>
              <div style={sectionGridStyle}>
                <button style={btnAdminAction} onClick={fetchAttendance}>List Attendance</button>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <input placeholder="Working days" value={attendanceWorking} onChange={e => setAttendanceWorking(e.target.value)} style={adminInputStyle} />
                  <input placeholder="Leave days" value={attendanceLeave} onChange={e => setAttendanceLeave(e.target.value)} style={adminInputStyle} />
                  <button style={btnAdminAction} disabled={!targetEmployeeId} onClick={updateAttendance}>Update Attendance</button>
                </div>
                
              </div>
            </section>
            <section style={adminSectionStyle}>
              <h4 style={sectionTitleStyle}>Employee Admin</h4>
              <div style={sectionGridStyle}>
                <button style={btnAdminAction} disabled={!targetEmployeeId} onClick={deleteEmployee}>Delete Employee</button>
              </div>
            </section>
          </div>
          <p style={{ fontSize: 12, marginTop: '0.75rem', color: '#94a3b8' }}>Leave ID fields blank to act on your own user. Adjust year/month for period-specific emails.</p>
        </div>
      )}
      {isAdmin && (
        <div style={{ border: '1px solid #ddd', padding: '1rem', marginBottom: '1.5rem' }}>
          <h3>Create Employee</h3>
          <form onSubmit={submitEmployee} style={{ display: 'grid', gap: '0.5rem', gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))' }}>
            <input placeholder="Email" value={empForm.email} onChange={e => updateEmpField('email', e.target.value)} required />
            <input placeholder="Password" type="password" value={empForm.password} onChange={e => updateEmpField('password', e.target.value)} required />
            <input placeholder="First Name" value={empForm.first_name} onChange={e => updateEmpField('first_name', e.target.value)} required />
            <input placeholder="Last Name" value={empForm.last_name} onChange={e => updateEmpField('last_name', e.target.value)} required />
            <input placeholder="CNP" value={empForm.cnp} onChange={e => updateEmpField('cnp', e.target.value)} required />
            <input placeholder="Role ID" value={empForm.role_id} onChange={e => updateEmpField('role_id', e.target.value)} required />
            <input placeholder="Manager ID (opt)" value={empForm.manager_id} onChange={e => updateEmpField('manager_id', e.target.value)} />
            <input placeholder="Department ID (opt)" value={empForm.department_id} onChange={e => updateEmpField('department_id', e.target.value)} />
            <input placeholder="Base Salary (opt)" value={empForm.base_salary} onChange={e => updateEmpField('base_salary', e.target.value)} />
            <input placeholder="Expected Days (opt)" value={empForm.expected_working_days} onChange={e => updateEmpField('expected_working_days', e.target.value)} />
            <button type="submit" disabled={empSubmitting} style={btnPrimaryStyle}>{empSubmitting ? 'Creating...' : 'Create Employee'}</button>
          </form>
        </div>
      )}
      {(isManager || isAdmin) && (
        <div style={{ border: '1px solid #ddd', padding: '1rem', marginBottom: '1.5rem' }}>
          <h3>Create Bonus</h3>
          <form onSubmit={submitBonus} style={{ display: 'grid', gap: '0.5rem', gridTemplateColumns: 'repeat(auto-fit, minmax(180px,1fr))' }}>
            <input placeholder="Employee ID" value={bonusForm.employee_id} onChange={e => updateBonusField('employee_id', e.target.value)} required />
            <input placeholder="Amount" value={bonusForm.amount} onChange={e => updateBonusField('amount', e.target.value)} required type="number" step="0.01" />
            <input placeholder="Description" value={bonusForm.description} onChange={e => updateBonusField('description', e.target.value)} required />
            <input placeholder="Date (YYYY-MM-DD)" value={bonusForm.date} onChange={e => updateBonusField('date', e.target.value)} />
            <button type="submit" disabled={bonusSubmitting} style={btnPrimaryStyle}>{bonusSubmitting ? 'Saving...' : 'Add Bonus'}</button>
          </form>
        </div>
      )}
      {bonuses.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h3>Bonuses</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={thStyle}>ID</th>
                <th style={thStyle}>Employee</th>
                <th style={thStyle}>Amount</th>
                <th style={thStyle}>Description</th>
                <th style={thStyle}>Date</th>
              </tr>
            </thead>
            <tbody>
              {bonuses.map(b => (
                <tr key={b.id}>
                  <td style={tdStyle}>{b.id}</td>
                  <td style={tdStyle}>{b.employee_id}</td>
                  <td style={tdStyle}>{b.amount}</td>
                  <td style={tdStyle}>{b.description}</td>
                  <td style={tdStyle}>{b.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {/* Data previews */}
      {isAdmin && (
        <div style={{ display: 'grid', gap: '1rem', marginTop: '1rem' }}>
          {rolesData.length > 0 && <div><h4>Roles</h4><pre style={preStyle}>{JSON.stringify(rolesData, null, 2)}</pre></div>}
          {departmentsData.length > 0 && <div><h4>Departments</h4><pre style={preStyle}>{JSON.stringify(departmentsData, null, 2)}</pre></div>}
          {managersData.length > 0 && <div><h4>Managers / Dept Managers</h4><pre style={preStyle}>{JSON.stringify(managersData, null, 2)}</pre></div>}
          {employeesData.length > 0 && (
            <div>
              <h4>Employees</h4>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={thStyle}>ID</th>
                    <th style={thStyle}>Email</th>
                    <th style={thStyle}>Name</th>
                    <th style={thStyle}>Role</th>
                    <th style={thStyle}>Dept</th>
                    <th style={thStyle}>Manager</th>
                  </tr>
                </thead>
                <tbody>
                  {employeesData.map((e: any) => (
                    <tr key={e.id}>
                      <td style={tdStyle}>{e.id}</td>
                      <td style={tdStyle}>{e.email}</td>
                      <td style={tdStyle}>{e.first_name} {e.last_name}</td>
                      <td style={tdStyle}>{e.role?.role || e.role}</td>
                      <td style={tdStyle}>{e.department_id || '-'}</td>
                      <td style={tdStyle}>{e.manager_id || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {attendanceData.length > 0 && <div><h4>Attendance ({periodYear}-{periodMonth})</h4><pre style={preStyle}>{JSON.stringify(attendanceData, null, 2)}</pre></div>}
          {aggregateData && <div><h4>Aggregate Data</h4><pre style={preStyle}>{JSON.stringify(aggregateData, null, 2)}</pre></div>}
        </div>
      )}
      {actionMsg && <div style={{ marginTop: '1rem', color: actionMsg.startsWith('Error') ? 'red' : 'green' }}>{actionMsg}</div>}
    </div>
  );
};

const btnStyle: React.CSSProperties = { padding: '0.6rem 1rem', background: '#1e3a8a', color: '#fff', border: 'none', cursor: 'pointer', borderRadius: 4 };
const btnPrimaryStyle: React.CSSProperties = { ...btnStyle, background: '#2563eb' };
const thStyle: React.CSSProperties = { textAlign: 'left', borderBottom: '1px solid #ddd', padding: '4px 6px' };
const tdStyle: React.CSSProperties = { borderBottom: '1px solid #eee', padding: '4px 6px', fontSize: 14 };
const adminLabelStyle: React.CSSProperties = { display: 'flex', flexDirection: 'column', fontSize: 13, gap: 4 };
const adminInputStyle: React.CSSProperties = { padding: '6px 8px', borderRadius: 4, border: '1px solid #334155', background: '#1e293b', color: '#f1f5f9' };
const btnAdminAction: React.CSSProperties = { ...btnStyle, background: '#0ea5e9' };
const preStyle: React.CSSProperties = { background: '#0f0f0f', color: '#e2e8f0', padding: '0.75rem', fontSize: 12, borderRadius: 4, overflowX: 'auto' };
const adminSectionStyle: React.CSSProperties = { border: '1px solid #243046', padding: '0.75rem', borderRadius: 4, background: '#1d2b3e' };
const sectionTitleStyle: React.CSSProperties = { margin: '0 0 0.5rem 0', fontSize: 14, letterSpacing: 0.5, textTransform: 'uppercase', color: '#93c5fd' };
const sectionGridStyle: React.CSSProperties = { display: 'grid', gap: '0.5rem', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))' };

export default Dashboard;
