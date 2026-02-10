/**
 * Knowledge Graph Hook - Data Management
 * 
 * Fetches and manages knowledge graph data from Neo4j API
 */

import { useState, useEffect } from 'react';
import { GraphNode, GraphEdge } from '../components/cortex/ForceSimulation';
import * as THREE from 'three';

interface UseKnowledgeGraphReturn {
    nodes: GraphNode[];
    edges: GraphEdge[];
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

/**
 * Hook to fetch and manage knowledge graph data
 */
export function useKnowledgeGraph(): UseKnowledgeGraphReturn {
    const [nodes, setNodes] = useState<GraphNode[]>([]);
    const [edges, setEdges] = useState<GraphEdge[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchGraph = async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch from backend API
            const response = await fetch('http://localhost:8008/api/v1/graph/full');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // Transform API data to graph format
            const transformedNodes: GraphNode[] = data.nodes.map((node: any) => ({
                id: node.id,
                label: node.properties.name || node.properties.label || node.id,
                type: node.labels[0] || 'default',
                position: new THREE.Vector3(0, 0, 0), // Will be set by simulation
                velocity: new THREE.Vector3(0, 0, 0),
                mass: 1.0,
                radius: 0.5 + (node.properties.importance || 0) * 0.5, // Size based on importance
                fixed: false,
                cluster: node.properties.cluster || node.labels[0],
            }));

            const transformedEdges: GraphEdge[] = data.relationships.map((rel: any) => ({
                id: rel.id,
                source: rel.startNodeId,
                target: rel.endNodeId,
                weight: rel.properties.weight || 1.0,
            }));

            setNodes(transformedNodes);
            setEdges(transformedEdges);
        } catch (err) {
            console.error('Failed to fetch knowledge graph:', err);
            setError(err instanceof Error ? err.message : 'Unknown error');

            // Fallback to demo data
            setNodes(generateDemoNodes());
            setEdges(generateDemoEdges());
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchGraph();
    }, []);

    return {
        nodes,
        edges,
        loading,
        error,
        refetch: fetchGraph,
    };
}

// ============================================================================
// Demo Data Generation (for development/demo)
// ============================================================================

function generateDemoNodes(): GraphNode[] {
    const concepts = [
        { label: 'Python', type: 'concept', cluster: 'languages' },
        { label: 'JavaScript', type: 'concept', cluster: 'languages' },
        { label: 'React', type: 'concept', cluster: 'frameworks' },
        { label: 'FastAPI', type: 'concept', cluster: 'frameworks' },
        { label: 'Machine Learning', type: 'concept', cluster: 'ai' },
        { label: 'Deep Learning', type: 'concept', cluster: 'ai' },
        { label: 'Neural Networks', type: 'concept', cluster: 'ai' },
        { label: 'Database', type: 'concept', cluster: 'storage' },
        { label: 'Neo4j', type: 'entity', cluster: 'storage' },
        { label: 'PostgreSQL', type: 'entity', cluster: 'storage' },
        { label: 'Web Development', type: 'concept', cluster: 'development' },
        { label: 'API Design', type: 'concept', cluster: 'development' },
        { label: 'Testing', type: 'action', cluster: 'quality' },
        { label: 'CI/CD', type: 'concept', cluster: 'devops' },
        { label: 'Docker', type: 'entity', cluster: 'devops' },
        { label: 'Kubernetes', type: 'entity', cluster: 'devops' },
        { label: 'Microservices', type: 'concept', cluster: 'architecture' },
        { label: 'REST API', type: 'concept', cluster: 'architecture' },
        { label: 'GraphQL', type: 'concept', cluster: 'architecture' },
        { label: 'Authentication', type: 'concept', cluster: 'security' },
    ];

    return concepts.map((concept, index) => ({
        id: `node-${index}`,
        label: concept.label,
        type: concept.type,
        position: new THREE.Vector3(0, 0, 0),
        velocity: new THREE.Vector3(0, 0, 0),
        mass: 1.0,
        radius: 0.5 + Math.random() * 0.3,
        fixed: false,
        cluster: concept.cluster,
    }));
}

function generateDemoEdges(): GraphEdge[] {
    // Define relationships between concepts
    const relationships = [
        { source: 0, target: 3, weight: 0.9 },  // Python - FastAPI
        { source: 1, target: 2, weight: 0.9 },  // JavaScript - React
        { source: 0, target: 4, weight: 0.7 },  // Python - ML
        { source: 4, target: 5, weight: 0.9 },  // ML - Deep Learning
        { source: 5, target: 6, weight: 0.8 },  // Deep Learning - Neural Networks
        { source: 3, target: 11, weight: 0.6 }, // FastAPI - API Design
        { source: 8, target: 7, weight: 0.7 },  // Neo4j - Database
        { source: 9, target: 7, weight: 0.7 },  // PostgreSQL - Database
        { source: 2, target: 10, weight: 0.8 }, // React - Web Dev
        { source: 10, target: 11, weight: 0.6 }, // Web Dev - API Design
        { source: 14, target: 13, weight: 0.8 }, // Docker - CI/CD
        { source: 15, target: 13, weight: 0.8 }, // Kubernetes - CI/CD
        { source: 16, target: 17, weight: 0.7 }, // Microservices - REST API
        { source: 17, target: 18, weight: 0.5 }, // REST API - GraphQL
        { source: 11, target: 19, weight: 0.6 }, // API Design - Auth
        { source: 14, target: 15, weight: 0.9 }, // Docker - Kubernetes
        { source: 0, target: 1, weight: 0.4 },  // Python - JavaScript
        { source: 12, target: 13, weight: 0.7 }, // Testing - CI/CD
    ];

    return relationships.map((rel, index) => ({
        id: `edge-${index}`,
        source: `node-${rel.source}`,
        target: `node-${rel.target}`,
        weight: rel.weight,
    }));
}
