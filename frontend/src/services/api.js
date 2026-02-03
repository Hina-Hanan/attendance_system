import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// User APIs
export const getUsers = () => api.get('/users/');
export const getUser = (userId) => api.get(`/users/${userId}`);
export const getTotalUsers = () => api.get('/users/count/total');
export const registerUser = (username, files) => {
  const formData = new FormData();
  formData.append('username', username);
  files.forEach((file, index) => {
    const name = file.name || `capture_${index + 1}.jpg`;
    formData.append('files', file, name);
  });
  return api.post('/auth/register', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

// Authentication APIs
// Pass a single file (no spoof) or an array of 3+ files (spoof/liveness check then face match)
export const authenticateFace = (fileOrFiles) => {
  const formData = new FormData();
  const files = Array.isArray(fileOrFiles) ? fileOrFiles : [fileOrFiles];
  files.forEach((file, index) => {
    const name = file.name || `frame_${index + 1}.jpg`;
    formData.append('files', file, name);
  });
  return api.post('/auth/authenticate', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const punchAttendance = (userId, action) => {
  return api.post('/auth/punch', {
    user_id: userId,
    action: action, // 'punch_in' or 'punch_out'
  });
};

// Attendance APIs
export const getAllAttendance = (limit = 100) => api.get(`/attendance/?limit=${limit}`);
export const getTodayAttendance = () => api.get('/attendance/today');
export const getUserAttendance = (userId, limit = 100) => 
  api.get(`/attendance/user/${userId}?limit=${limit}`);
export const getUserAttendanceByNumber = (userNumber, date = null, limit = 200) => {
  const params = new URLSearchParams();
  params.append('limit', String(limit));
  if (date) params.append('date', date);
  return api.get(`/attendance/user-number/${userNumber}?${params.toString()}`);
};
export const getAttendanceByDate = (date, limit = 500) => {
  const params = new URLSearchParams();
  params.append('date', date);
  params.append('limit', String(limit));
  return api.get(`/attendance/by-date?${params.toString()}`);
};

// Export APIs
export const exportAttendanceCSV = (startDate, endDate) => {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  return api.get(`/export/csv?${params.toString()}`, {
    responseType: 'blob',
  });
};

export default api;
