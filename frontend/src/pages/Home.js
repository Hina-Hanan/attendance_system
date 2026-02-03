import React, { useState } from 'react';
import Dashboard from '../components/Dashboard';
import UserRegistration from '../components/UserRegistration';
import FaceAuth from '../components/FaceAuth';

const Home = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div>
      <div style={{ 
        background: 'white', 
        padding: '20px', 
        borderBottom: '2px solid #667eea',
        marginBottom: '20px'
      }}>
        <div className="container" style={{ display: 'flex', gap: '20px' }}>
          <button
            className={`btn ${activeTab === 'dashboard' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={`btn ${activeTab === 'register' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('register')}
          >
            Register User
          </button>
          <button
            className={`btn ${activeTab === 'auth' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setActiveTab('auth')}
          >
            Face Auth
          </button>
        </div>
      </div>

      {activeTab === 'dashboard' && <Dashboard key={refreshKey} />}
      {activeTab === 'register' && <UserRegistration onSuccess={handleRefresh} />}
      {activeTab === 'auth' && <FaceAuth onSuccess={handleRefresh} />}
    </div>
  );
};

export default Home;
