import React, { useState } from 'react';
import UserManagement from '../components/UserManagement';
import ClaimUpload from '../components/ClaimUpload';
import ClaimDetails from '../components/ClaimDetails';

const AdminDashboard = () => {
    const [view, setView] = useState('users'); // 'users', 'upload', or 'details'

    return (
        <div>
            <h2>Admin Dashboard</h2>
            <nav>
                <button onClick={() => setView('users')} style={{ marginRight: '10px' }}>
                    User Management
                </button>
                <button onClick={() => setView('upload')} style={{ marginRight: '10px' }}>
                    Claim Upload
                </button>
                <button onClick={() => setView('details')}>
                    View All Claims
                </button>
            </nav>
            <hr />

            {/* Conditionally render the selected component */}
            {view === 'users' && <UserManagement />}
            {view === 'upload' && <ClaimUpload />}
            {view === 'details' && <ClaimDetails />}
        </div>
    );
};
export default AdminDashboard;