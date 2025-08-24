import React, { useState } from 'react';
import UserManagement from '../components/UserManagement';
import ClaimUpload from '../components/ClaimUpload';

const AdminDashboard = () => {
    const [view, setView] = useState('users');

    return (
        <div>
            <h2>Admin Dashboard</h2>
            <nav>
                <button onClick={() => setView('users')}>User Management</button>
                <button onClick={() => setView('claims')}>Claim Upload</button>
            </nav>
            <hr />
            {view === 'users' && <UserManagement />}
            {view === 'claims' && <ClaimUpload />}
        </div>
    );
};

export default AdminDashboard;