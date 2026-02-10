/**
 * AgentModal Component
 * 
 * Dialog wrapper for creating/editing agents.
 * Handles API calls and state management.
 */

'use client';

import React from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { AgentForm, AgentFormData } from './AgentForm';
import { apiClient } from '@/lib/api/client';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

// ============================================================================
// Component Props
// ============================================================================

interface AgentModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    agentId?: string;
    initialData?: Partial<AgentFormData>;
}

// ============================================================================
// AgentModal Component
// ============================================================================

export function AgentModal({
    open,
    onOpenChange,
    agentId,
    initialData
}: AgentModalProps) {
    const [isLoading, setIsLoading] = React.useState(false);
    const queryClient = useQueryClient();

    const isEditMode = Boolean(agentId);

    const handleSubmit = async (data: AgentFormData) => {
        setIsLoading(true);

        try {
            if (isEditMode) {
                // Update existing agent
                await apiClient.put(`/v1/agents/${agentId}`, data);
                toast.success('Agent updated successfully!');
            } else {
                // Create new agent
                await apiClient.post('/v1/agents/', data);
                toast.success('Agent created successfully!');
            }

            // Invalidate agents query to refresh the list
            await queryClient.invalidateQueries({ queryKey: ['agents'] });

            // Close modal
            onOpenChange(false);
        } catch (error: any) {
            console.error('Failed to save agent:', error);
            toast.error(
                error.response?.data?.detail ||
                `Failed to ${isEditMode ? 'update' : 'create'} agent`
            );
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>
                        {isEditMode ? 'Edit Agent' : 'Create New Agent'}
                    </DialogTitle>
                    <DialogDescription>
                        {isEditMode
                            ? 'Update the agent configuration and capabilities.'
                            : 'Define a new AI agent with custom capabilities and behavior.'}
                    </DialogDescription>
                </DialogHeader>

                <AgentForm
                    initialData={initialData}
                    onSubmit={handleSubmit}
                    onCancel={() => onOpenChange(false)}
                    isLoading={isLoading}
                />
            </DialogContent>
        </Dialog>
    );
}
