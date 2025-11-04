import React, { useState, useEffect } from "react";
import api from "../api/axiosConfig";

const MemberDashboard = () => {
	const [claims, setClaims] = useState([]);
	const [editedClaims, setEditedClaims] = useState([]);
	const [isModalOpen, setIsModalOpen] = useState(false);
	const [changesToConfirm, setChangesToConfirm] = useState(null);

	const fetchMyClaims = async () => {
		try {
			const response = await api.get("/member/claims");
			setClaims(response.data);

			// Initialize the edited state with the latest note's content
			setEditedClaims(
				response.data.map((c) => {
					const latestNote =
						c.notes?.length > 0 ? c.notes[c.notes.length - 1].content : "";
					return { ...c, noteContent: latestNote };
				})
			);
		} catch (error) {
			console.error("Could not fetch claims.", error);
		}
	};

	useEffect(() => {
		fetchMyClaims();
	}, []);

	const handleInputChange = (claimId, field, value) => {
		setEditedClaims((prevClaims) =>
			prevClaims.map((claim) =>
				claim.id === claimId ? { ...claim, [field]: value } : claim
			)
		);
	};

	const handleSaveClick = (claimId) => {
		const originalClaim = claims.find((c) => c.id === claimId);
		const editedClaim = editedClaims.find((c) => c.id === claimId);

		const originalNote =
			originalClaim.notes?.length > 0
				? originalClaim.notes[originalClaim.notes.length - 1].content
				: "";

		const changes = {};
		if (originalClaim.status !== editedClaim.status) {
			changes.status = { from: originalClaim.status, to: editedClaim.status };
		}
		if (originalNote !== editedClaim.noteContent.trim()) {
			changes.note = editedClaim.noteContent.trim();
		}

		if (Object.keys(changes).length > 0) {
			setChangesToConfirm({ claimId, ...changes });
			setIsModalOpen(true);
		}
	};

	const handleConfirmSave = async () => {
		if (!changesToConfirm) return;

		const { claimId, status, note } = changesToConfirm;
		const payload = {};
		if (status) payload.status = status.to;
		if (note || note === "") payload.note = note; // Allow sending empty note to clear it

		// Members can update status and add notes
		await api.put(`/member/claims/${claimId}`, payload);

		setIsModalOpen(false);
		setChangesToConfirm(null);
		fetchMyClaims();
	};

	const handleCancel = () => {
		setIsModalOpen(false);
		setChangesToConfirm(null);
		// Revert any pending changes
		const revertedClaims = claims.map((c) => {
			const latestNote =
				c.notes?.length > 0 ? c.notes[c.notes.length - 1].content : "";
			return { ...c, noteContent: latestNote };
		});
		setEditedClaims(revertedClaims);
	};

	return (
		<div>
			<h2>My Assigned Claims</h2>
			<table>
				<thead>
					<tr>
						<th>Claim ID</th>
						<th>Patient</th>
						<th>Amount</th>
						<th>Date of Service</th>
						<th>Status</th>
						<th>Last Note</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{editedClaims.map((claim, index) => {
						const originalClaim = claims[index];
						const originalNote =
							originalClaim?.notes?.length > 0
								? originalClaim.notes[originalClaim.notes.length - 1].content
								: "";
						const hasChanges =
							originalClaim?.status !== claim.status ||
							originalNote !== claim.noteContent?.trim();

						return (
							<tr key={claim.id}>
								<td>{claim.claim_id}</td>
								<td>{claim.patient_name}</td>
								<td>₹{claim.amount}</td>
								<td>{claim.dos}</td>
								<td>
									<select
										value={claim.status}
										onChange={(e) =>
											handleInputChange(claim.id, "status", e.target.value)
										}
									>
										<option value="NEW">NEW</option>
										<option value="In Progress">In Progress</option>
										<option value="On Hold">On Hold</option>
										<option value="Submitted">Submitted</option>
									</select>
								</td>
								<td>
									<input
										type="text"
										placeholder="Add new note..."
										value={claim.noteContent}
										onChange={(e) =>
											handleInputChange(claim.id, "noteContent", e.target.value)
										}
									/>
									{/* Optional: Show all notes below for audit */}
									{claim.notes && claim.notes.length > 0 && (
										<ul style={{ fontSize: "0.8em", color: "gray" }}>
											{claim.notes.map((n, i) => (
												<li key={i}>
													{n.content} ({n.timestamp})
												</li>
											))}
										</ul>
									)}
								</td>
								<td>
									<button
										onClick={() => handleSaveClick(claim.id)}
										disabled={!hasChanges}
									>
										Save
									</button>
								</td>
							</tr>
						);
					})}
				</tbody>
			</table>

			{isModalOpen && changesToConfirm && (
				<div className="modal-overlay">
					<div className="modal-content">
						<h3>Confirm Changes</h3>
						<ul>
							{changesToConfirm.status && (
								<li>
									<b>Status:</b> {changesToConfirm.status.from} →{" "}
									<b>{changesToConfirm.status.to}</b>
								</li>
							)}
							{changesToConfirm.note !== undefined && (
								<li>
									<b>Note Updated To:</b> {changesToConfirm.note}
								</li>
							)}
						</ul>
						<div className="modal-actions">
							<button onClick={handleConfirmSave}>Confirm</button>
							<button type="button" onClick={handleCancel}>
								Cancel
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default MemberDashboard;
