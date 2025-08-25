import React from 'react';
import { Navigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';

const PrivateRoute = ({ children, role }) => {
    
    const token = localStorage.getItem('token');
    if (!token) return <Navigate to="/login" />;

    try {
        const decoded = jwtDecode(token);
        if (decoded.exp * 1000 < Date.now()) {
            localStorage.clear();
            return <Navigate to="/login" />;
        }
        if (role && decoded.role !== role) {
            localStorage.clear();
            return <Navigate to="/login" />;
        }
    } catch (error) {
        localStorage.clear();
        return <Navigate to="/login" />;
    }
    return children;
};

export default PrivateRoute;