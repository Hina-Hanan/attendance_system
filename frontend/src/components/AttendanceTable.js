import React from 'react';

const AttendanceTable = ({ attendance, onRefresh, emptyMessage = 'No attendance records found' }) => {
  const formatDateTime = (dateTime) => {
    if (!dateTime) return '-';
    return new Date(dateTime).toLocaleString();
  };

  const getStatus = (record) => {
    if (record.is_absent) {
      return <span style={{ color: '#6c757d' }}>Absent</span>;
    }
    if (record.punch_in_time && record.punch_out_time) {
      return <span style={{ color: '#28a745' }}>Completed</span>;
    } else if (record.punch_in_time) {
      return <span style={{ color: '#ffc107' }}>Active</span>;
    } else {
      return <span style={{ color: '#dc3545' }}>Not Started</span>;
    }
  };

  if (!attendance || attendance.length === 0) {
    return (
      <div className="empty-state">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>User ID</th>
            <th>Username</th>
            <th>Date</th>
            <th>Punch In</th>
            <th>Punch Out</th>
            <th>Duration</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {attendance.map((record) => (
            <tr key={record.attendance_id}>
              <td>{record.user_number != null ? record.user_number : '—'}</td>
              <td>{record.username}</td>
              <td>{record.date}</td>
              <td>{formatDateTime(record.punch_in_time)}</td>
              <td>{formatDateTime(record.punch_out_time)}</td>
              <td>{record.total_duration || '-'}</td>
              <td>{getStatus(record)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AttendanceTable;
