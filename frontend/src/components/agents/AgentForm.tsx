'use client';

/**
 * AgentForm Component
 * 
 * Reusable form for creating and editing agents with full validation.
 * Uses Zod for runtime type safety and react-hook-form for state management.
 */

'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { X } from 'lucide-react';

// ============================================================================
// Zod Schema
// ============================================================================

const agentFormSchema = z.object({
    name: z.string()
        .min(3, 'Name must be at least 3 characters')
        .max(50, 'Name must be less than 50 characters'),

    agent_type: z.enum([
        'data_analyst',
        'designer',
        'translator',
        'financial_advisor',
        'researcher',
        'code_generator',
        'general'
    ]),

    system_prompt: z.string()
        .min(20, 'System prompt must be at least 20 characters')
        .max(2000, 'System prompt must be less than 2000 characters'),

    capabilities: z.array(z.string())
        .min(1, 'Agent must have at least one capability')
        .max(10, 'Maximum 10 capabilities allowed'),

    status: z.enum(['active', 'inactive', 'training']),

    temperature: z.number()
        .min(0, 'Temperature must be between 0 and 2')
        .max(2, 'Temperature must be between 0 and 2'),
});

export type AgentFormData = z.infer<typeof agentFormSchema>;

// ============================================================================
// Component Props
// ============================================================================

interface AgentFormProps {
    initialData?: Partial<AgentFormData>;
    onSubmit: (data: AgentFormData) => Promise<void>;
    onCancel: () => void;
    isLoading?: boolean;
}

// ============================================================================
// AgentForm Component
// ============================================================================

export function AgentForm({
    initialData,
    onSubmit,
    onCancel,
    isLoading = false
}: AgentFormProps) {
    const {
        register,
        handleSubmit,
        formState: { errors },
        setValue,
        watch,
    } = useForm<AgentFormData>({
        resolver: zodResolver(agentFormSchema),
        defaultValues: {
            name: initialData?.name || '',
            agent_type: initialData?.agent_type || 'general',
            system_prompt: initialData?.system_prompt || '',
            capabilities: initialData?.capabilities || [],
            status: initialData?.status || 'active',
            temperature: initialData?.temperature || 0.7,
        },
    });

    const capabilities = watch('capabilities');
    const [newCapability, setNewCapability] = React.useState('');

    const addCapability = () => {
        if (newCapability.trim() && !capabilities.includes(newCapability.trim())) {
            setValue('capabilities', [...capabilities, newCapability.trim()]);
            setNewCapability('');
        }
    };

    const removeCapability = (cap: string) => {
        setValue('capabilities', capabilities.filter(c => c !== cap));
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Name */}
            <div>
                <Label htmlFor="name">Agent Name *</Label>
                <Input
                    id="name"
                    {...register('name')}
                    placeholder="e.g., Data Analyst Pro"
                    className="mt-1"
                />
                {errors.name && (
                    <p className="mt-1 text-sm text-red-500">{errors.name.message}</p>
                )}
            </div>

            {/* Agent Type */}
            <div>
                <Label htmlFor="agent_type">Agent Type *</Label>
                <select
                    id="agent_type"
                    {...register('agent_type')}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                    <option value="general">General Purpose</option>
                    <option value="data_analyst">Data Analyst</option>
                    <option value="designer">Designer</option>
                    <option value="translator">Translator</option>
                    <option value="financial_advisor">Financial Advisor</option>
                    <option value="researcher">Researcher</option>
                    <option value="code_generator">Code Generator</option>
                </select>
                {errors.agent_type && (
                    <p className="mt-1 text-sm text-red-500">{errors.agent_type.message}</p>
                )}
            </div>

            {/* System Prompt */}
            <div>
                <Label htmlFor="system_prompt">System Prompt *</Label>
                <Textarea
                    id="system_prompt"
                    {...register('system_prompt')}
                    placeholder="You are a helpful assistant that..."
                    rows={6}
                    className="mt-1"
                />
                {errors.system_prompt && (
                    <p className="mt-1 text-sm text-red-500">{errors.system_prompt.message}</p>
                )}
            </div>

            {/* Capabilities */}
            <div>
                <Label>Capabilities *</Label>
                <div className="mt-2 flex gap-2">
                    <Input
                        value={newCapability}
                        onChange={(e) => setNewCapability(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                addCapability();
                            }
                        }}
                        placeholder="e.g., data_visualization"
                    />
                    <Button type="button" onClick={addCapability} variant="outline">
                        Add
                    </Button>
                </div>

                <div className="mt-2 flex flex-wrap gap-2">
                    {capabilities.map((cap) => (
                        <Badge key={cap} variant="secondary" className="gap-1">
                            {cap}
                            <button
                                type="button"
                                onClick={() => removeCapability(cap)}
                                className="ml-1 rounded-full hover:bg-destructive/20"
                            >
                                <X className="h-3 w-3" />
                            </button>
                        </Badge>
                    ))}
                </div>

                {errors.capabilities && (
                    <p className="mt-1 text-sm text-red-500">{errors.capabilities.message}</p>
                )}
            </div>

            {/* Temperature */}
            <div>
                <Label htmlFor="temperature">Temperature: {watch('temperature')}</Label>
                <input
                    id="temperature"
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    {...register('temperature', { valueAsNumber: true })}
                    className="mt-1 w-full"
                />
                <div className="mt-1 flex justify-between text-xs text-muted-foreground">
                    <span>Precise (0.0)</span>
                    <span>Balanced (1.0)</span>
                    <span>Creative (2.0)</span>
                </div>
            </div>

            {/* Status */}
            <div>
                <Label htmlFor="status">Status</Label>
                <select
                    id="status"
                    {...register('status')}
                    className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="training">Training</option>
                </select>
            </div>

            {/* Form Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
                <Button
                    type="button"
                    variant="outline"
                    onClick={onCancel}
                    disabled={isLoading}
                >
                    Cancel
                </Button>
                <Button type="submit" disabled={isLoading}>
                    {isLoading ? 'Saving...' : initialData ? 'Update Agent' : 'Create Agent'}
                </Button>
            </div>
        </form>
    );
}
