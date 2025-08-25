import React from 'react';
import { Navigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';

const PrivateRoute = ({ children, role }) => {
    console.log({role});
    
    const token = localStorage.getItem('token');
    console.log({token});

    if (!token) return <Navigate to="/login" />;

    try {
        const decoded = jwtDecode(token);
        if (decoded.exp * 1000 < Date.now()) {
            localStorage.clear();
            console.log('Token has expired.');
            return <Navigate to="/login" />;
        }
        if (role && decoded.role !== role) {
            console.log(role, decoded.role);
            localStorage.clear();
            
            console.log('User does not have the required role.');
            return <Navigate to="/login" />;
        }
    } catch (error) {
        console.error('Error decoding token:', error);
        localStorage.clear();
        return <Navigate to="/login" />;
    }
    return children;
};

export default PrivateRoute;