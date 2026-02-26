declare module 'd3-force-3d' {
    export function forceSimulation<NodeDatum = unknown, LinkDatum = unknown>(
        nodes?: NodeDatum[],
        dimensions?: number
    ): Simulation<NodeDatum, LinkDatum>;
    export function forceManyBody<NodeDatum = unknown>(): Force<NodeDatum>;
    export function forceLink<NodeDatum = unknown, LinkDatum = unknown>(links?: LinkDatum[]): ForceLink<NodeDatum, LinkDatum>;
    export function forceCenter<NodeDatum = unknown>(x?: number, y?: number, z?: number): Force<NodeDatum>;

    export interface Simulation<NodeDatum, LinkDatum> {
        nodes(nodes?: NodeDatum[]): this;
        alpha(alpha?: number): this;
        alphaMin(min?: number): this;
        alphaDecay(decay?: number): this;
        alphaTarget(target?: number): this;
        velocityDecay(decay?: number): this;
        force(name: string, force?: Force<NodeDatum>): this;
        find(x: number, y: number, z?: number, radius?: number): NodeDatum | undefined;
        on(typename: string, listener?: (this: Simulation<NodeDatum, LinkDatum>) => void): this;
        stop(): this;
        tick(iterations?: number): this;
    }

    export interface Force<NodeDatum> {
        (alpha: number): void;
        initialize(nodes: NodeDatum[]): void;
        strength(strength?: number | ((d: NodeDatum, i: number, data: NodeDatum[]) => number)): this;
    }

    export interface ForceLink<NodeDatum, LinkDatum> extends Force<NodeDatum> {
        links(links?: LinkDatum[]): this | LinkDatum[];
        id(id?: (d: NodeDatum, i: number, data: NodeDatum[]) => string | number): this;
        distance(distance?: number | ((d: LinkDatum, i: number, data: LinkDatum[]) => number)): this;
    }
}
