import type { Component } from 'svelte';
import SlopeGrid from './SlopeGrid.svelte';
import ParCoords from './ParCoords.svelte';
import QuadrantMap from './QuadrantMap.svelte';

/**
 * chart type -> component, keyed by the `chart` field a producer writes into its
 * own `<name>.data.json`.
 *
 * THE PRODUCER NAMES ITS CHART TYPE and this maps the name to a drawing. Adding
 * a figure of an EXISTING shape costs nothing here -- write the data file and it
 * renders. Adding a new SHAPE costs one component and one line in this map,
 * which is the honest price and is why it is a map rather than an if-chain: the
 * cost should be visible in one place.
 */
export const CHARTS: Record<string, Component<any>> = {
	slopes: SlopeGrid,
	parcoords: ParCoords,
	quadrants: QuadrantMap
};
