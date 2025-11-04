import React, { useState, useEffect } from "react";
import api from "../api/axiosConfig";
const RulesManagement = () => {
	const [rules, setRules] = useState([]);
	const [isModalOpen, setIsModalOpen] = useState(false);
	const [editingRule, setEditingRule] = useState(null);
	const [formData, setFormData] = useState({
		criteria_type: "",
		criteria_value: "",
		strategy: "",
		priority: 1,
	});
	useEffect(() => {
		fetchRules();
	}, []);
	const fetchRules = async () => {
		const response = await api.get("/admin/rules");
		setRules(response.data);
	};
	const openEditModal = (rule = null) => {
		setEditingRule(rule);
		setFormData(
			rule || {
				criteria_type: "",
				criteria_value: "",
				strategy: "",
				priority: 1,
			}
		);
		setIsModalOpen(true);
	};
	const handleSave = async (e) => {
		e.preventDefault();
		if (editingRule) {
			await api.put(`/admin/rules/${editingRule.id}`, formData);
		} else {
			await api.post("/admin/rules", formData);
		}
		setIsModalOpen(false);
		fetchRules();
	};
	const handleDelete = async (ruleId) => {
		if (window.confirm("Delete rule?")) {
			await api.delete(`/admin/rules/${ruleId}`);
			fetchRules();
		}
	};
	return (
		<div>
			<h3>Manage Assignment Rules</h3>
			<button onClick={() => openEditModal()}>Add Rule</button>
			<table>
				<thead>
					<tr>
						<th>Criteria Type</th>
						<th>Value</th>
						<th>Strategy</th>
						<th>Priority</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{rules.map((rule) => (
						<tr key={rule.id}>
							<td>{rule.criteria_type}</td>
							<td>{rule.criteria_value}</td>
							<td>{rule.strategy}</td>
							<td>{rule.priority}</td>
							<td>
								<button onClick={() => openEditModal(rule)}>Edit</button>
								<button onClick={() => handleDelete(rule.id)}>Delete</button>
							</td>
						</tr>
					))}
				</tbody>
			</table>
			{isModalOpen && (
				<div className="modal-overlay">
					<div className="modal-content">
						<h3>{editingRule ? "Edit" : "Add"} Rule</h3>
						<form onSubmit={handleSave}>
							<div>
								<label>Criteria Type: </label>
								<input
									name="criteria_type"
									value={formData.criteria_type}
									onChange={(e) =>
										setFormData({ ...formData, criteria_type: e.target.value })
									}
									required
								/>
							</div>
							<div>
								<label>Criteria Value: </label>
								<input
									name="criteria_value"
									value={formData.criteria_value}
									onChange={(e) =>
										setFormData({ ...formData, criteria_value: e.target.value })
									}
								/>
							</div>
							<div>
								<label>Strategy: </label>
								<select
									name="strategy"
									value={formData.strategy}
									onChange={(e) =>
										setFormData({ ...formData, strategy: e.target.value })
									}
									required
								>
									<option value="age">Age</option>
									<option value="seniority">Seniority</option>
									<option value="payer">Payer</option>
								</select>
							</div>
							<div>
								<label>Priority: </label>
								<input
									type="number"
									name="priority"
									value={formData.priority}
									onChange={(e) =>
										setFormData({
											...formData,
											priority: parseInt(e.target.value),
										})
									}
								/>
							</div>
							<button type="submit">Save</button>
							<button type="button" onClick={() => setIsModalOpen(false)}>
								Cancel
							</button>
						</form>
					</div>
				</div>
			)}
		</div>
	);
};
export default RulesManagement;
