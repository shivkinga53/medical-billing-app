import React, { useState } from "react";
import UserManagement from "../components/UserManagement";
import ClaimUpload from "../components/ClaimUpload";
import ClaimDetails from "../components/ClaimDetails";
import RulesManagement from "../components/RulesManagement";

const AdminDashboard = () => {
	const [view, setView] = useState("users"); // 'users', 'upload', or 'details'

	return (
		<div>
			<h2>Admin Dashboard</h2>
			<nav>
				<button
					onClick={() => setView("users")}
					style={{ marginRight: "10px" }}
				>
					User Management
				</button>
				<button
					onClick={() => setView("rules")}
					style={{ marginRight: "10px" }}
				>
					Rules Management
				</button>
				<button
					onClick={() => setView("upload")}
					style={{ marginRight: "10px" }}
				>
					Claim Upload
				</button>
				<button onClick={() => setView("details")}>View All Claims</button>
				<button
					onClick={() => setView("stats")}
					style={{ marginRight: "10px" }}
				>
					View Statistics
				</button>
			</nav>
			<hr />

			{/* Conditionally render the selected component */}
			{view === "users" && <UserManagement />}
			{view === "rules" && <RulesManagement />}
			{view === "upload" && <ClaimUpload />}
			{view === "details" && <ClaimDetails />}
			{view === "stats" && (
				<div>
					<h3>Statistics</h3>
					{/* Fetch and display on mount */}
					{/* Use useState/useEffect similar to ClaimDetails */}
				</div>
			)}
		</div>
	);
};
export default AdminDashboard;
