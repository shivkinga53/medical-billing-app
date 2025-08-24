import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';
import { jwtDecode } from 'jwt-decode';

const LoginPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const response = await api.post('/login', { username, password });
            const { token } = response.data;
            const decoded = jwtDecode(token);

            localStorage.setItem('token', token);
            localStorage.setItem('role', decoded.role);
            
            if (decoded.role === 'Admin') {
                navigate('/admin');
            } else {
                navigate('/member');
            }
        } catch (err) {
            setError(err.response?.data?.message || 'Login failed.');
        }
    };

    return (
        <div>
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
                <div>Username: <input type="text" value={username} onChange={e => setUsername(e.target.value)} /></div>
                <div>Password: <input type="password" value={password} onChange={e => setPassword(e.target.value)} /></div>
                <button type="submit">Login</button>
            </form>
            {error && <p className="error">{error}</p>}
        </div>
    );
};

export default LoginPage;