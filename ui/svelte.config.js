import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: {
		//: Built INTO the package, so `malignment.serve` can hand out a built app
		//: with no separate static host and no build step at serve time. The
		//: archive did the same and it is the one part of its wiring that never
		//: caused a problem.
		adapter: adapter({
			pages: '../malignment/ui_dist',
			assets: '../malignment/ui_dist',
			fallback: 'index.html'
		}),
		paths: {
			relative: true
		}
	}
};

export default config;
