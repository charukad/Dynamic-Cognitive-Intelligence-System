declare module 'd3-force-3d' {
    export function forceSimulation<NodeDatum = any, LinkDatum = any>(nodes?: NodeDatum[]): Simulation<NodeDatum, LinkDatum>;
    export function forceManyBody<NodeDatum = any>(): Force<NodeDatum, any>;
    export function forceLink<NodeDatum = any, LinkDatum = any>(links?: LinkDatum[]): ForceLink<NodeDatum, LinkDatum>;
    export function forceCenter<NodeDatum = any>(x?: number, y?: number, z?: number): Force<NodeDatum, any>;

    export interface Simulation<NodeDatum, LinkDatum> {
        nodes(nodes?: NodeDatum[]): this;
        alpha(alpha?: number): this;
        alphaMin(min?: number): this;
        alphaDecay(decay?: number): this;
        alphaTarget(target?: number): this;
        velocityDecay(decay?: number): this;
        force(name: string, force?: Force<NodeDatum, LinkDatum>): this;
        find(x: number, y: number, z?: number, radius?: number): NodeDatum | undefined;
        on(typename: string, listener?: (this: Simulation<NodeDatum, LinkDatum>) => void): this;
        stop(): this;
        tick(iterations?: number): this;
    }

    export interface Force<NodeDatum, LinkDatum> {
        (alpha: number): void;
        initialize(nodes: NodeDatum[]): void;
        strength(strength?: number | ((d: NodeDatum, i: number, data: NodeDatum[]) => number)): this | any;
    }

    export interface ForceLink<NodeDatum, LinkDatum> extends Force<NodeDatum, LinkDatum> {
        links(links?: LinkDatum[]): this | LinkDatum[];
        id(id?: (d: NodeDatum, i: number, data: NodeDatum[]) => string | number): this;
        distance(distance?: number | ((d: LinkDatum, i: number, data: LinkDatum[]) => number)): this | any;
    }
}
