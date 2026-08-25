<!--
  A "Save PNG" button that exports the nearest SVG ancestor at 300 dpi.

  Drop this inside any chart component, inside or next to the chart area.
  It finds the closest `<svg>` element, serializes it, renders to a
  canvas at `dpi` scale, and triggers a download.

  ## WHY NOT CANVAS-BASED CHARTS

  Canvas charts (QuadrantMap) draw to a `<canvas>` element, not SVG.
  For those, `getContext('2d').canvas.toBlob()` works directly, but the
  LayerChart canvas renderer doesn't expose the canvas element bindably.
  This component works for SVG charts only and says so if it can't find one.

  ## 300 DPI

  The default browser SVG is 96 dpi. We render at `dpi / 96` scale so a
  figure that is 800px wide on screen becomes 2500px at 300 dpi — the
  standard for print submission.
-->
<script lang="ts">
	let { label = 'Save PNG', dpi = 300, filename = 'figure' }: {
		label?: string;
		dpi?: number;
		filename?: string;
	} = $props();

	let btn: HTMLButtonElement;
	let saving = $state(false);

	async function save() {
		if (saving) return;
		saving = true;
		try {
			const container = btn.closest('.chart-area') ?? btn.closest('figure') ?? btn.parentElement;
			const svg = container?.querySelector('svg');
			if (!svg) {
				console.warn('ExportPng: no <svg> found');
				saving = false;
				return;
			}

			const clone = svg.cloneNode(true) as SVGSVGElement;

			const styles = document.querySelectorAll('style');
			const styleText = Array.from(styles).map((s) => s.textContent ?? '').join('\n');
			const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
			styleEl.textContent = styleText;
			clone.insertBefore(styleEl, clone.firstChild);

			const computed = getComputedStyle(svg);
			const bgColor = computed.backgroundColor || '#ffffff';

			// Force sans-serif on all text for clean export
			const fontStyle = document.createElementNS('http://www.w3.org/2000/svg', 'style');
			fontStyle.textContent = 'text, .tick text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif !important; }';
			clone.insertBefore(fontStyle, clone.firstChild);

			const bbox = svg.getBoundingClientRect();
			clone.setAttribute('width', String(bbox.width));
			clone.setAttribute('height', String(bbox.height));
			if (!clone.getAttribute('viewBox')) {
				clone.setAttribute('viewBox', `0 0 ${bbox.width} ${bbox.height}`);
			}

			const serializer = new XMLSerializer();
			const svgStr = serializer.serializeToString(clone);
			const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
			const url = URL.createObjectURL(blob);

			const scale = dpi / 96;
			const canvas = document.createElement('canvas');
			canvas.width = Math.round(bbox.width * scale);
			canvas.height = Math.round(bbox.height * scale);
			const ctx = canvas.getContext('2d')!;

			ctx.fillStyle = bgColor === 'rgba(0, 0, 0, 0)' ? '#ffffff' : bgColor;
			ctx.fillRect(0, 0, canvas.width, canvas.height);

			const img = new Image();
			img.onload = () => {
				ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
				URL.revokeObjectURL(url);

				canvas.toBlob((pngBlob) => {
					if (!pngBlob) { saving = false; return; }
					const a = document.createElement('a');
					a.href = URL.createObjectURL(pngBlob);
					a.download = `${filename}_${dpi}dpi.png`;
					a.click();
					URL.revokeObjectURL(a.href);
					saving = false;
				}, 'image/png');
			};
			img.onerror = () => {
				URL.revokeObjectURL(url);
				saving = false;
			};
			img.src = url;
		} catch (e) {
			console.error('ExportPng:', e);
			saving = false;
		}
	}
</script>

<button class="export-btn" onclick={save} bind:this={btn} disabled={saving}>
	{saving ? 'saving...' : label}
</button>

<style>
	.export-btn {
		position: absolute;
		top: 4px;
		right: 4px;
		z-index: 20;
		background: var(--panel, #fff);
		border: 1px solid var(--rule, #ddd);
		border-radius: 4px;
		padding: 2px 8px;
		font-size: 0.65rem;
		color: var(--text-3, #888);
		cursor: pointer;
		opacity: 0.5;
		transition: opacity 0.15s;
	}
	.export-btn:hover { opacity: 1; }
	.export-btn:disabled { cursor: wait; opacity: 0.3; }
</style>
