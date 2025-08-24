import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
	plugins: [react()],
	server: {
		proxy: {
			// String shorthand for simple cases
			// Forward any request starting with /api to the backend server
			"/api": {
				target: "http://localhost:3001", // Your Express server's address
				changeOrigin: true, // Recommended for virtual hosts
				secure: false, // Optional: if your backend is not https
			},
		},
	},
});
