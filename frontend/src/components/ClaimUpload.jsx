import React, { useState } from 'react';
import api from '../api/axiosConfig';

const ClaimUpload = () => {
    const [file, setFile] = useState(null);
    const [validationResult, setValidationResult] = useState(null);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleFileChange = e => setFile(e.target.files[0]);

    const handleValidate = async () => {
        if (!file) { setError('Please select a file first.'); return; }
        setIsLoading(true); setError(''); setValidationResult(null);
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await api.post('/admin/claims/upload-validate', formData);
            setValidationResult(response.data);
        } catch (err) {
            setError(err.response?.data?.message || 'Validation failed.');
            setValidationResult(err.response?.data || null);
        } finally {
            setIsLoading(false);
        }
    };

    const handleExecute = async () => {
        setIsLoading(true); setError('');
        try {
            // FIX: The backend expects a key named 'assignable_claims'
            const response = await api.post('/admin/claims/upload-execute', {
                assignable_claims: validationResult.assignable_claims
            });
            
            alert(response.data.message);
            setValidationResult(null); // Reset after execution
        } catch (err) {
            setError(err.response?.data?.message || 'Execution failed.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div>
            <h3>Upload and Assign Claims</h3>
            <input type="file" onChange={handleFileChange} accept=".xlsx, .csv" />
            <button onClick={handleValidate} disabled={isLoading}>
                {isLoading ? 'Validating...' : 'Validate File'}
            </button>
            {error && <p className="error">{error}</p>}

            {validationResult && (
                <div>
                    <h4>Validation Result</h4>
                    {validationResult.unassignable_claims?.length > 0 ? (
                        <div>
                            <p className="error">The following claims could not be assigned:</p>
                            <ul>
                                {validationResult.unassignable_claims.map((c, i) => <li key={i}><b>{c.claim_id}:</b> {c.reason}</li>)}
                            </ul>
                        </div>
                    ) : (
                        <div>
                            <p className="success">All {validationResult.assignable_claims?.length} claims can be assigned. Please review the plan below.</p>
                            
                            {/* --- NEW: Display the assignment plan in a table --- */}
                            {/* This table serves as the "confirmation dialog" for the Admin */}
                            <table style={{ marginTop: '15px' }}>
                                <thead>
                                    <tr>
                                        <th>Claim ID</th>
                                        <th>Will Be Assigned To</th>
                                        <th>Assignment Strategy</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {validationResult.assignable_claims.map((c, i) => (
                                        <tr key={i}>
                                            <td>{c.claim_id}</td>
                                            <td>{c.assign_to}</td>
                                            <td>{c.strategy}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            
                            <button onClick={handleExecute} disabled={isLoading} style={{ marginTop: '15px' }}>
                                {isLoading ? 'Assigning...' : 'Confirm & Execute Assignment'}
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ClaimUpload;