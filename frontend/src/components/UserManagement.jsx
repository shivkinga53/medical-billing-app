import React, { useState, useEffect } from "react";
import api from "../api/axiosConfig";

const UserManagement = () => {
	const [users, setUsers] = useState([]);
	const [allSkills, setAllSkills] = useState([]);
	const [isModalOpen, setIsModalOpen] = useState(false);
	const [editingUser, setEditingUser] = useState(null);
	const [formData, setFormData] = useState({});

	// Fetch all users and all available skills on component mount
	useEffect(() => {
		fetchUsers();
		fetchAllSkills();
	}, []);

	const fetchUsers = async () => {
		const response = await api.get("/admin/users");
		setUsers(response.data);
	};

	const fetchAllSkills = async () => {
		const response = await api.get("/admin/skills");
		setAllSkills(response.data);
	};

	// --- Event Handlers ---

	const handleStatusToggle = async (userId, currentStatus) => {
		// Admin will have the ability to mark their status active or inactive
		await api.put(`/admin/users/${userId}`, { is_active: !currentStatus });
		fetchUsers();
	};

	const handleDelete = async (userId) => {
		// Admin will have the ability to delete the user
		if (window.confirm("Are you sure you want to delete this user?")) {
			alert(`(Placeholder) Deleting user ${userId}`);
			// In a real app: await api.delete(`/admin/users/${userId}`);
			fetchUsers();
		}
	};

	const openEditModal = (user) => {
		setEditingUser(user);
        console.log(user);
        
		setFormData({
			role: user.role || "",
			max_daily_claims: user.max_daily_claims || 0,
			seniority: user.seniority || 0,
			skill_ids: user.skills
				? allSkills.filter((s) => user.skills.includes(s.name)).map((s) => s.id)
				: [],
		});
		setIsModalOpen(true);
	};

	const handleFormChange = (e) => {
		setFormData({ ...formData, [e.target.name]: e.target.value });
	};

	const handleSkillChange = (skillId) => {
		const newSkillIds = formData.skill_ids.includes(skillId)
			? formData.skill_ids.filter((id) => id !== skillId)
			: [...formData.skill_ids, skillId];
		setFormData({ ...formData, skill_ids: newSkillIds });
	};

	const handleSaveChanges = async (e) => {
		e.preventDefault();
		await api.put(`/admin/users/${editingUser.id}`, formData);
		setIsModalOpen(false);
		setEditingUser(null);
		fetchUsers();
	};

	return (
		<div>
			<h3>Manage Users</h3>
			<table>
				{/* Table rendering remains the same... */}
				<thead>
					<tr>
						<th>Name</th>
						<th>Username</th>
						<th>Role</th>
						<th>Status</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{users.map((user) => (
						<tr key={user.id}>
							<td>{user.name}</td>
							<td>{user.username}</td>
							<td>{user.role || "N/A"}</td>
							<td>{user.is_active ? "Active" : "Inactive"}</td>
							<td>
								<button onClick={() => openEditModal(user)}>Edit</button>
								<button
									onClick={() => handleStatusToggle(user.id, user.is_active)}
								>
									{user.is_active ? "Deactivate" : "Activate"}
								</button>
								<button onClick={() => handleDelete(user.id)}>Delete</button>
							</td>
						</tr>
					))}
				</tbody>
			</table>

			{isModalOpen && editingUser && (
				<div className="modal-overlay">
					<div className="modal-content">
						<h3>Edit User: {editingUser.name}</h3>
						<form onSubmit={handleSaveChanges}>
							<div>
								{/* Admin will assign role */}
								<label>Role: </label>
								<input
									name="role"
									value={formData.role}
									onChange={handleFormChange}
								/>
							</div>
							<div>
								{/* Admin will assign max_daily_claims */}
								<label>Max Daily Claims: </label>
								<input
									type="number"
									name="max_daily_claims"
									value={formData.max_daily_claims}
									onChange={handleFormChange}
								/>
							</div>
							<div>
								{/* Admin will assign seniority */}
								<label>Seniority: </label>
								<input
									type="number"
									name="seniority"
									value={formData.seniority}
									onChange={handleFormChange}
								/>
							</div>
							<div>
								{/* Admin will assign skills */}
								<label>Skills:</label>
								<div className="skills-container">
									{allSkills.map((skill) => (
										<div key={skill.id} className="skill-checkbox">
											<input
												type="checkbox"
												id={skill.id}
												checked={formData.skill_ids.includes(skill.id)}
												onChange={() => handleSkillChange(skill.id)}
											/>
											<label htmlFor={skill.id}>{skill.name}</label>
										</div>
									))}
								</div>
							</div>
							<div className="modal-actions">
								<button type="submit">Save Changes</button>
								<button type="button" onClick={() => setIsModalOpen(false)}>
									Cancel
								</button>
							</div>
						</form>
					</div>
				</div>
			)}
		</div>
	);
};

export default UserManagement;
