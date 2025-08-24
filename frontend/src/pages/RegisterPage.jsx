import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axiosConfig';

const RegisterPage = () => {
    const [name, setName] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleRegister = async (e) => {
        e.preventDefault();
        try {
            // Members will create an account with normal creds
            const response = await api.post('/register', { name, username, password });
            setMessage(response.data.message);
            setTimeout(() => navigate('/login'), 3000);
        } catch (err) {
            setError(err.response?.data?.message || 'Registration failed.');
        }
    };

    return (
        <div>
            <h2>Register New Member</h2>
            <form onSubmit={handleRegister}>
                <div>Name: <input type="text" value={name} onChange={e => setName(e.target.value)} required /></div>
                <div>Username: <input type="text" value={username} onChange={e => setUsername(e.target.value)} required /></div>
                <div>Password: <input type="password" value={password} onChange={e => setPassword(e.target.value)} required /></div>
                <button type="submit">Register</button>
            </form>
            {message && <p className="success">{message}</p>}
            {error && <p className="error">{error}</p>}
        </div>
    );
};

export default RegisterPage;