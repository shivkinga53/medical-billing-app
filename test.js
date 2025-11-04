[
	"Medicare",
	"BlueCross",
	"UnitedHealth",
	"Aetna",
	"Medicaid",
	"Kaiser",
	"Cigna",
].forEach((name) => {
	fetch("http://localhost:5000/api/admin/skills", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNmUyZjllODgtODM3Mi00NGQwLThmZWYtODNkMjI1NTYwYmM1Iiwicm9sZSI6IkFkbWluIiwiZXhwIjoxNzYyMjgyMzAyfQ.KD4h18FXwy4xtRCDcy5vwDrcf977Cc5zFqHGsRnEwjY",
		},
		body: JSON.stringify({ name }),
	})
		.then((r) => r.json())
		.then(console.log); // Expect: {message: "Skill created"}
});
