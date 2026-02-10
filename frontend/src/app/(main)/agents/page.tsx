"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { AgentsListSkeleton } from "@/components/loading-states";
import { APIError } from "@/components/error-boundary";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BrainCircuitIcon, PlusIcon, PencilIcon, Trash2Icon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { AgentModal } from "@/components/agents/AgentModal";
import { AgentFormData } from "@/components/agents/AgentForm";
import { toast } from "sonner";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface AgentResponse {
    id: string;
    name: string;
    agent_type: string;
    status: string;
    system_prompt: string;
    capabilities?: string[];
    temperature?: number;
}

export default function AgentsPage() {
    const queryClient = useQueryClient();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingAgent, setEditingAgent] = useState<AgentResponse | null>(null);
    const [deletingAgent, setDeletingAgent] = useState<AgentResponse | null>(null);

    const { data: agents, isLoading, error, refetch } = useQuery<AgentResponse[]>({
        queryKey: ["agents"],
        queryFn: () => apiClient.get("/v1/agents/"),
    });

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: (agentId: string) => apiClient.delete(`/v1/agents/${agentId}`),
        onSuccess: () => {
            toast.success("Agent deleted successfully");
            queryClient.invalidateQueries({ queryKey: ["agents"] });
            setDeletingAgent(null);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to delete agent");
        },
    });

    const handleCreate = () => {
        setEditingAgent(null);
        setIsModalOpen(true);
    };

    const handleEdit = (agent: AgentResponse) => {
        setEditingAgent(agent);
        setIsModalOpen(true);
    };

    const handleDelete = (agent: AgentResponse) => {
        setDeletingAgent(agent);
    };

    const confirmDelete = () => {
        if (deletingAgent) {
            deleteMutation.mutate(deletingAgent.id);
        }
    };

    if (isLoading) {
        return (
            <div className="container mx-auto p-6">
                <h1 className="mb-6 text-3xl font-bold">Agents</h1>
                <AgentsListSkeleton />
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto p-6">
                <h1 className="mb-6 text-3xl font-bold">Agents</h1>
                <APIError
                    message="Failed to load agents"
                    onRetry={() => refetch()}
                />
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold">Agents</h1>
                    <p className="mt-1 text-muted-foreground">
                        Manage your AI agents ({agents?.length || 0} total)
                    </p>
                </div>
                <Button className="gap-2" onClick={handleCreate}>
                    <PlusIcon className="h-4 w-4" />
                    Create Agent
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {agents?.map((agent) => (
                    <Card key={agent.id} className="p-6 hover:shadow-lg transition-shadow">
                        <div className="flex items-start gap-4">
                            <div className="rounded-full bg-primary/10 p-3">
                                <BrainCircuitIcon className="h-6 w-6 text-primary" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between gap-2">
                                    <h3 className="font-semibold truncate">{agent.name}</h3>
                                    <div className="flex gap-1">
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => handleEdit(agent)}
                                        >
                                            <PencilIcon className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => handleDelete(agent)}
                                        >
                                            <Trash2Icon className="h-4 w-4 text-destructive" />
                                        </Button>
                                    </div>
                                </div>
                                <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                                    {agent.system_prompt}
                                </p>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    <Badge variant="secondary">{agent.agent_type}</Badge>
                                    <Badge variant="outline">{agent.status}</Badge>
                                    {agent.capabilities && agent.capabilities.length > 0 && (
                                        <Badge variant="default">
                                            {agent.capabilities.length} capabilities
                                        </Badge>
                                    )}
                                </div>
                            </div>
                        </div>
                    </Card>
                ))}
            </div>

            {/* Create/Edit Modal */}
            <AgentModal
                open={isModalOpen}
                onOpenChange={setIsModalOpen}
                agentId={editingAgent?.id}
                initialData={editingAgent || undefined}
            />

            {/* Delete Confirmation Dialog */}
            <AlertDialog open={!!deletingAgent} onOpenChange={() => setDeletingAgent(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                        <AlertDialogDescription>
                            This will permanently delete the agent "{deletingAgent?.name}".
                            This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={confirmDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            Delete
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}

