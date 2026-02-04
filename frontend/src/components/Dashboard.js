import React, { useMemo, useState, useEffect } from 'react';
import { getTotalUsers, getTodayAttendance, exportAttendanceCSV, getUserAttendanceByNumber, getAttendanceByDate, getUsers, getDailySummary } from '../services/api';
import AttendanceTable from './AttendanceTable';

const Dashboard = () => {
  const [totalUsers, setTotalUsers] = useState(0);
  const [allUsers, setAllUsers] = useState([]);
  const [todayAttendance, setTodayAttendance] = useState([]);
  const [todayFilter, setTodayFilter] = useState('all'); // all | active | punched_out | absent
  const [lookupUserNumber, setLookupUserNumber] = useState('');
  const [lookupDate, setLookupDate] = useState('');
  const [userAttendance, setUserAttendance] = useState([]);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [lookupDailySummary, setLookupDailySummary] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [usersRes, attendanceRes, allUsersRes] = await Promise.all([
        getTotalUsers(),
        getTodayAttendance(),
        getUsers(),
      ]);
      setTotalUsers(usersRes.data.total_users);
      setTodayAttendance(attendanceRes.data);
      setAllUsers(allUsersRes.data || []);
    } catch (err) {
      const msg = err.response?.status === 500
        ? 'Server error. Ensure the backend is running and the database has the latest schema.'
        : err.code === 'ERR_NETWORK' || err.message === 'Network Error'
          ? 'Cannot reach the server. Is the backend running at http://localhost:8000?'
          : err.response?.data?.detail || err.message || 'Failed to load dashboard data';
      setError(msg);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const todayKey = useMemo(() => new Date().toISOString().split('T')[0], []);

  const activeToday = useMemo(
    () => todayAttendance.filter((a) => a.punch_in_time && !a.punch_out_time),
    [todayAttendance]
  );

  const punchedOutToday = useMemo(
    () => todayAttendance.filter((a) => a.punch_in_time && a.punch_out_time),
    [todayAttendance]
  );

  const absentToday = useMemo(() => {
    const present = new Set((todayAttendance || []).map((a) => a.user_id));
    return (allUsers || [])
      .filter((u) => u && u.user_id && !present.has(u.user_id))
      .map((u) => ({
        attendance_id: u.user_id, // synthetic id for table key
        user_id: u.user_id,
        user_number: u.user_number ?? null,
        username: u.username,
        date: todayKey,
        punch_in_time: null,
        punch_out_time: null,
        total_duration: null,
        is_absent: true,
      }));
  }, [allUsers, todayAttendance, todayKey]);

  const filteredToday = useMemo(() => {
    if (todayFilter === 'active') return activeToday;
    if (todayFilter === 'punched_out') return punchedOutToday;
    if (todayFilter === 'absent') return absentToday;
    return todayAttendance;
  }, [todayFilter, activeToday, punchedOutToday, absentToday, todayAttendance]);

  const handleExportCSV = async () => {
    try {
      setExporting(true);
      const response = await exportAttendanceCSV();
      
      // Create blob and download
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `attendance_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export CSV');
      console.error(err);
    } finally {
      setExporting(false);
    }
  };

  const handleLookup = async () => {
    const n = String(lookupUserNumber).trim();
    const d = String(lookupDate || '').trim();

    // Mode A: date-only lookup
    if (!n && d) {
      try {
        setLookupLoading(true);
        setLookupError(null);
        const [res, summaryRes] = await Promise.all([
          getAttendanceByDate(d),
          getDailySummary(d).catch(() => ({ data: { summaries: [] } })),
        ]);
        setUserAttendance(res.data || []);
        setLookupDailySummary(summaryRes.data?.summaries || []);
      } catch (err) {
        const msg = err.response?.data?.detail || err.message || 'Failed to load attendance for that date';
        setLookupError(msg);
        setUserAttendance([]);
        setLookupDailySummary([]);
        console.error(err);
      } finally {
        setLookupLoading(false);
      }
      return;
    }

    // Mode B: user_number (optionally with date)
    if (!n) {
      setLookupError('Enter a User ID (number), or pick a date to search all attendance for that day.');
      return;
    }
    if (!/^\d+$/.test(n)) {
      setLookupError('User ID must be a number (e.g. 1, 2, 3...).');
      return;
    }

    try {
      setLookupLoading(true);
      setLookupError(null);
      const res = await getUserAttendanceByNumber(Number(n), d || null);
      setUserAttendance(res.data || []);
      if (d) {
        const summaryRes = await getDailySummary(d).catch(() => ({ data: { summaries: [] } }));
        setLookupDailySummary(summaryRes.data?.summaries || []);
      } else {
        setLookupDailySummary([]);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to load user attendance';
      setLookupError(msg);
      setUserAttendance([]);
      setLookupDailySummary([]);
      console.error(err);
    } finally {
      setLookupLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Face Authentication Attendance System</h1>
        <p>Admin Dashboard</p>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
          <button type="button" className="btn btn-secondary" style={{ marginLeft: '12px', marginTop: '8px' }} onClick={loadData}>
            Retry
          </button>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <h3>{totalUsers}</h3>
          <p>Total Users</p>
        </div>
        <div className="stat-card">
          <h3>{todayAttendance.length}</h3>
          <p>Today's Attendance</p>
        </div>
        <div className="stat-card">
          <h3>
            {activeToday.length}
          </h3>
          <p>Currently Active</p>
        </div>
        <div className="stat-card">
          <h3>{absentToday.length}</h3>
          <p>Absent Today</p>
        </div>
      </div>

      <div className="section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>Today's Attendance</h2>
          <button 
            className="btn btn-primary" 
            onClick={handleExportCSV}
            disabled={exporting}
          >
            {exporting ? 'Exporting...' : 'Export CSV'}
          </button>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '12px' }}>
          <button className={`btn ${todayFilter === 'all' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTodayFilter('all')}>
            All ({todayAttendance.length})
          </button>
          <button className={`btn ${todayFilter === 'active' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTodayFilter('active')}>
            Active ({activeToday.length})
          </button>
          <button className={`btn ${todayFilter === 'punched_out' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTodayFilter('punched_out')}>
            Punched Out ({punchedOutToday.length})
          </button>
          <button className={`btn ${todayFilter === 'absent' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTodayFilter('absent')}>
            Absent ({absentToday.length})
          </button>
        </div>
        <AttendanceTable
          attendance={filteredToday}
          onRefresh={loadData}
          emptyMessage={todayFilter === 'absent' ? 'No absent users today' : 'No records for this filter'}
        />
      </div>

      <div className="section">
        <h2>Attendance Lookup</h2>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '15px' }}>
          <input
            type="text"
            value={lookupUserNumber}
            onChange={(e) => setLookupUserNumber(e.target.value)}
            placeholder="User ID (number) e.g. 1 (optional if date is selected)"
            style={{ padding: '10px', border: '1px solid #ddd', borderRadius: '5px', minWidth: '260px' }}
          />
          <input
            type="date"
            value={lookupDate}
            onChange={(e) => setLookupDate(e.target.value)}
            style={{ padding: '10px', border: '1px solid #ddd', borderRadius: '5px' }}
          />
          <button className="btn btn-primary" onClick={handleLookup} disabled={lookupLoading}>
            {lookupLoading ? 'Searching...' : 'Search'}
          </button>
          {userAttendance.length > 0 && (
            <span style={{ color: '#666' }}>
              Showing {userAttendance.length} record(s)
            </span>
          )}
        </div>

        {lookupError && (
          <div className="alert alert-error" style={{ marginBottom: '15px' }}>
            {lookupError}
          </div>
        )}

        {lookupDailySummary.length > 0 && (lookupDate || userAttendance.length > 0) && (
          <div style={{ marginBottom: '15px', padding: '12px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
            <strong>Total active hours for selected date (per user):</strong>
            <ul style={{ margin: '8px 0 0', paddingLeft: '20px' }}>
              {lookupDailySummary.map((s) => (
                <li key={s.user_id}>
                  {s.user_number != null ? `#${s.user_number} ` : ''}{s.username}: <strong>{s.total_duration}</strong>
                  {s.sessions && s.sessions.length > 1 && (
                    <span style={{ color: '#666', fontSize: '0.9em' }}> ({s.sessions.length} sessions)</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        <AttendanceTable
          attendance={userAttendance}
          onRefresh={handleLookup}
          emptyMessage={
            !lookupUserNumber && lookupDate
              ? 'No attendance records for that date'
              : lookupDate
                ? 'No records for that user on that date'
                : 'No records for that user'
          }
        />
      </div>
    </div>
  );
};

export default Dashboard;
