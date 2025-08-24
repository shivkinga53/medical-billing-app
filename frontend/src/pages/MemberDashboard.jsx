import React, { useState, useEffect } from 'react';
import api from '../api/axiosConfig';

const MemberDashboard = () => {
    const [claims, setClaims] = useState([]);

    const fetchMyClaims = async () => {
        try {
            // Members can log in to view the claims assigned to them
            const response = await api.get('/member/claims');
            setClaims(response.data);
        } catch (error) { console.error("Could not fetch claims.", error); }
    };

    useEffect(() => {
        fetchMyClaims();
    }, []);

    const handleStatusChange = async (claimId, newStatus) => {
        await api.put(`/member/claims/${claimId}`, { status: newStatus });
        fetchMyClaims(); // Refresh claims
    };

    return (
        <div>
            <h2>My Assigned Claims</h2>
            <table>
                <thead>
                    <tr><th>Claim ID</th><th>Patient</th><th>Payer</th><th>Status</th></tr>
                </thead>
                <tbody>
                    {claims.map(claim => (
                        <tr key={claim.id}>
                            <td>{claim.claim_id}</td><td>{claim.patient_name}</td><td>{claim.payer}</td>
                            <td>
                                {/* Members can update status */}
                                <select value={claim.status} onChange={(e) => handleStatusChange(claim.id, e.target.value)}>
                                    <option value="Assigned">Assigned</option>
                                    <option value="In Progress">In Progress</option>
                                    <option value="On Hold">On Hold</option>
                                    <option value="Submitted">Submitted</option>
                                </select>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default MemberDashboard;