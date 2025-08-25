import React, { useState, useEffect } from 'react';
import api from '../api/axiosConfig';

const ClaimDetails = () => {
    const [claims, setClaims] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchClaims = async () => {
            try {
                setIsLoading(true);
                // Admins can upload or view a patient claims table
                const response = await api.get('/admin/claims');
                setClaims(response.data);
                setError('');
            } catch (err) {
                setError('Failed to fetch claim details.');
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchClaims();
    }, []);

    if (isLoading) {
        return <p>Loading claim details...</p>;
    }

    if (error) {
        return <p className="error">{error}</p>;
    }

    return (
        <div>
            <h3>All Claims in Database</h3>
            <table>
                <thead>
                    <tr>
                        <th>Claim ID</th>
                        <th>Patient Name</th>
                        <th>Payer</th>
                        <th>Amount</th>
                        <th>Date of Service</th>
                        <th>Status</th>
                        <th>Assigned To</th>
                    </tr>
                </thead>
                <tbody>
                    {claims.map(claim => (
                        <tr key={claim.id}>
                            <td>{claim.claim_id}</td>
                            <td>{claim.patient_name}</td>
                            <td>{claim.payer}</td>
                            <td>₹{claim.amount}</td>
                            <td>{claim.dos}</td>
                            <td>{claim.status}</td>
                            <td>{claim.assignee}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default ClaimDetails;