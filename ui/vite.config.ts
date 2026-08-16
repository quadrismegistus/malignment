import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

//: The API port is a default, not a constant: two seats running the app at once
//: on one machine is the normal case here, and a hardcoded port makes the second
//: one silently talk to the first one's server.
const API_PORT = process.env.MALIGNMENT_API_PORT || '8431';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		//: 0.0.0.0 so the app is reachable over Tailscale from the laptop. Note
		//: what this costs: `navigator.clipboard` is undefined outside a secure
		//: context, so any copy button must use the execCommand path. The archive
		//: shipped a copy button that silently did nothing for weeks because of
		//: exactly this.
		host: '0.0.0.0',
		proxy: {
			'/api': {
				target: `http://127.0.0.1:${API_PORT}`,
				rewrite: (path) => path.replace(/^\/api/, '')
			}
		}
	}
});
