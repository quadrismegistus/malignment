//: NO SSR AND NO PRERENDER OF DATA. The app is a reader for a store that lives
//: on this machine; there is no build-time snapshot to prerender and a stale one
//: would be worse than none. `prerender` here emits the SHELL only, which is what
//: adapter-static needs to produce an index.html.
export const prerender = true;
export const ssr = false;
