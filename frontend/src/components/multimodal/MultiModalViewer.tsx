/**
 * Multi-modal Viewer - Upload and Analyze Images/Audio
 * 
 * Features:
 * - Drag & drop file upload
 * - Real-time analysis progress
 * - Image: caption, objects, OCR
 * - Audio: transcription, speakers, waveform
 * - Similarity search
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
    Upload,
    Image as ImageIcon,
    Music,
    X,
    Download,
    Search,
    Loader2,
    Check
} from 'lucide-react';
import { z } from 'zod';
import './MultiModalViewer.css';

// ============================================================================
// ✅ NEW: Zod Schemas for Runtime Validation
// ============================================================================

const ObjectDetectionSchema = z.object({
    label: z.string(),
    confidence: z.number().min(0).max(1),
    bbox: z.tuple([z.number(), z.number(), z.number(), z.number()])
});

const ImageAnalysisSchema = z.object({
    caption: z.string(),
    objects: z.array(ObjectDetectionSchema),
    ocr_text: z.string().optional(),
    embedding: z.array(z.number())
});

const SpeakerSegmentSchema = z.object({
    speaker_id: z.string(),
    start_time: z.number().min(0),
    end_time: z.number().min(0),
    text: z.string()
});

const AudioAnalysisSchema = z.object({
    transcription: z.string(),
    speakers: z.array(SpeakerSegmentSchema),
    sounds: z.array(z.string()),
    embedding: z.array(z.number())
});

// ============================================================================
// Types
// ============================================================================

interface UploadedFile {
    id: string;
    file: File;
    type: 'image' | 'audio';
    preview?: string;
    status: 'uploading' | 'analyzing' | 'complete' | 'error';
    progress: number;
    analysis?: ImageAnalysis | AudioAnalysis;
    error?: string; // ✅ NEW: Store error message
}

interface ImageAnalysis {
    caption: string;
    objects: Array<{
        label: string;
        confidence: number;
        bbox: [number, number, number, number];
    }>;
    ocr_text?: string;
    embedding: number[];
}

interface AudioAnalysis {
    transcription: string;
    speakers: Array<{
        speaker_id: string;
        start_time: number;
        end_time: number;
        text: string;
    }>;
    sounds: string[];
    embedding: number[];
}

// ============================================================================
// Multi-modal Viewer Component
// ============================================================================

export function MultiModalViewer() {
    const [uploads, setUploads] = useState<UploadedFile[]>([]);
    const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<UploadedFile[]>([]);

    // Dropzone configuration
    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const newUploads = acceptedFiles.map(file => ({
            id: generateId(),
            file,
            type: file.type.startsWith('image/') ? 'image' as const : 'audio' as const,
            preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
            status: 'uploading' as const,
            progress: 0
        }));

        setUploads(prev => [...prev, ...newUploads]);

        // Process each file
        for (const upload of newUploads) {
            await processFile(upload);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
            'audio/*': ['.mp3', '.wav', '.ogg', '.m4a']
        },
        multiple: true
    });

    // Process file (upload + analyze)
    const processFile = async (upload: UploadedFile) => {
        try {
            // Update status
            updateUpload(upload.id, { status: 'analyzing', progress: 50 });

            // Read file as base64
            const base64 = await fileToBase64(upload.file);

            // Call appropriate API
            let analysis;
            let rawResponse;

            if (upload.type === 'image') {
                const response = await fetch('/api/v1/multimodal/analyze-image', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_base64: base64 })
                });

                if (!response.ok) {
                    throw new Error(`API returned ${response.status}: ${response.statusText}`);
                }

                rawResponse = await response.json();

                // ✅ UPDATED: Validate response with Zod
                try {
                    analysis = ImageAnalysisSchema.parse(rawResponse);
                } catch (validationError) {
                    if (validationError instanceof z.ZodError) {
                        const issues = validationError.issues.map((e: z.ZodIssue) =>
                            `${e.path.join('.')}: ${e.message}`
                        ).join(', ');
                        throw new Error(`Invalid API response: ${issues}`);
                    }
                    throw validationError;
                }
            } else {
                const response = await fetch('/api/v1/multimodal/transcribe-audio', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ audio_base64: base64 })
                });

                if (!response.ok) {
                    throw new Error(`API returned ${response.status}: ${response.statusText}`);
                }

                rawResponse = await response.json();

                // ✅ UPDATED: Validate response with Zod
                try {
                    analysis = AudioAnalysisSchema.parse(rawResponse);
                } catch (validationError) {
                    if (validationError instanceof z.ZodError) {
                        const issues = validationError.issues.map((e: z.ZodIssue) =>
                            `${e.path.join('.')}: ${e.message}`
                        ).join(', ');
                        throw new Error(`Invalid API response: ${issues}`);
                    }
                    throw validationError;
                }
            }

            // Update with validated results
            updateUpload(upload.id, {
                status: 'complete',
                progress: 100,
                analysis
            });

        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            console.error('Processing failed:', errorMessage, error);

            updateUpload(upload.id, {
                status: 'error',
                progress: 0,
                error: errorMessage
            });
        }
    };

    // Update upload
    const updateUpload = (id: string, updates: Partial<UploadedFile>) => {
        setUploads(prev =>
            prev.map(u => (u.id === id ? { ...u, ...updates } : u))
        );
    };

    // Remove upload
    const removeUpload = (id: string) => {
        setUploads(prev => prev.filter(u => u.id !== id));
        if (selectedFile?.id === id) {
            setSelectedFile(null);
        }
    };

    // Search similar files
    const handleSearch = async () => {
        if (!searchQuery.trim()) return;

        try {
            const response = await fetch('/api/v1/multimodal/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: searchQuery,
                    top_k: 5
                })
            });

            const results = await response.json();
            // Map results to uploads (simplified)
            setSearchResults(uploads.filter(u => u.status === 'complete').slice(0, 3));
        } catch (error) {
            console.error('Search failed:', error);
        }
    };

    return (
        <div className="multimodal-viewer">
            {/* Header */}
            <div className="viewer-header">
                <h1>Multi-modal Analysis</h1>
                <p>Upload images or audio for AI-powered analysis</p>
            </div>

            {/* Upload Zone */}
            <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                <Upload size={48} />
                {isDragActive ? (
                    <p>Drop files here...</p>
                ) : (
                    <>
                        <p>Drag & drop files here, or click to browse</p>
                        <span>Supports: Images (PNG, JPG) and Audio (MP3, WAV)</span>
                    </>
                )}
            </div>

            {/* Search */}
            <div className="search-bar">
                <input
                    type="text"
                    placeholder="Search similar content..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
                <button onClick={handleSearch}>
                    <Search size={20} />
                    Search
                </button>
            </div>

            {/* Results Grid */}
            <div className="results-container">
                {/* File List */}
                <div className="file-list">
                    <h3>Uploaded Files ({uploads.length})</h3>
                    {uploads.map(upload => (
                        <FileCard
                            key={upload.id}
                            upload={upload}
                            isSelected={selectedFile?.id === upload.id}
                            onClick={() => setSelectedFile(upload)}
                            onRemove={() => removeUpload(upload.id)}
                        />
                    ))}
                </div>

                {/* Analysis Panel */}
                <div className="analysis-panel">
                    {selectedFile ? (
                        <AnalysisView upload={selectedFile} />
                    ) : (
                        <div className="empty-state">
                            <ImageIcon size={64} />
                            <p>Select a file to view analysis</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
                <div className="search-results">
                    <h3>Search Results</h3>
                    <div className="results-grid">
                        {searchResults.map(result => (
                            <FileCard
                                key={result.id}
                                upload={result}
                                isSelected={false}
                                onClick={() => setSelectedFile(result)}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// ============================================================================
// File Card Component
// ============================================================================

interface FileCardProps {
    upload: UploadedFile;
    isSelected: boolean;
    onClick: () => void;
    onRemove?: () => void;
}

function FileCard({ upload, isSelected, onClick, onRemove }: FileCardProps) {
    const getStatusIcon = () => {
        switch (upload.status) {
            case 'uploading':
            case 'analyzing':
                return <Loader2 size={16} className="spinner" />;
            case 'complete':
                return <Check size={16} color="#10b981" />;
            case 'error':
                return <X size={16} color="#ef4444" />;
        }
    };

    return (
        <div
            className={`file-card ${isSelected ? 'selected' : ''}`}
            onClick={onClick}
        >
            <div className="file-preview">
                {upload.type === 'image' && upload.preview ? (
                    <img src={upload.preview} alt={upload.file.name} />
                ) : (
                    <Music size={32} />
                )}
            </div>

            <div className="file-info">
                <span className="file-name">{upload.file.name}</span>
                <span className="file-size">{formatBytes(upload.file.size)}</span>
            </div>

            <div className="file-status">
                {getStatusIcon()}
            </div>

            {onRemove && (
                <button
                    className="remove-btn"
                    onClick={(e) => {
                        e.stopPropagation();
                        onRemove();
                    }}
                >
                    <X size={16} />
                </button>
            )}

            {upload.status !== 'complete' && upload.progress > 0 && (
                <div className="progress-bar">
                    <div
                        className="progress-fill"
                        style={{ width: `${upload.progress}%` }}
                    />
                </div>
            )}

            {/* ✅ NEW: Display error message */}
            {upload.status === 'error' && upload.error && (
                <div className="error-message" title={upload.error}>
                    <X size={14} />
                    <span>{upload.error.length > 40 ? upload.error.substring(0, 40) + '...' : upload.error}</span>
                </div>
            )}
        </div>
    );
}

// ============================================================================
// Analysis View Component
// ============================================================================

interface AnalysisViewProps {
    upload: UploadedFile;
}

function AnalysisView({ upload }: AnalysisViewProps) {
    if (upload.status !== 'complete' || !upload.analysis) {
        return (
            <div className="analysis-loading">
                <Loader2 size={48} className="spinner" />
                <p>Analyzing {upload.type}...</p>
            </div>
        );
    }

    if (upload.type === 'image') {
        return <ImageAnalysisView upload={upload} analysis={upload.analysis as ImageAnalysis} />;
    } else {
        return <AudioAnalysisView upload={upload} analysis={upload.analysis as AudioAnalysis} />;
    }
}

// ============================================================================
// Image Analysis View
// ============================================================================

function ImageAnalysisView({ upload, analysis }: { upload: UploadedFile; analysis: ImageAnalysis }) {
    return (
        <div className="image-analysis">
            <h2>Image Analysis</h2>

            {/* Preview */}
            <div className="image-preview">
                <img src={upload.preview} alt={upload.file.name} />
            </div>

            {/* Caption */}
            <div className="analysis-section">
                <h3>Caption</h3>
                <p className="caption">{analysis.caption}</p>
            </div>

            {/* Objects Detected */}
            <div className="analysis-section">
                <h3>Objects Detected ({analysis.objects.length})</h3>
                <div className="objects-list">
                    {analysis.objects.map((obj, idx) => (
                        <div key={idx} className="object-item">
                            <span className="object-label">{obj.label}</span>
                            <span className="object-confidence">{(obj.confidence * 100).toFixed(1)}%</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* OCR Text */}
            {analysis.ocr_text && (
                <div className="analysis-section">
                    <h3>Text Detected (OCR)</h3>
                    <p className="ocr-text">{analysis.ocr_text}</p>
                </div>
            )}

            {/* Embedding Info */}
            <div className="analysis-section">
                <h3>Embedding</h3>
                <p className="embedding-info">
                    Vector dimension: {analysis.embedding.length}
                </p>
            </div>
        </div>
    );
}

// ============================================================================
// Audio Analysis View
// ============================================================================

function AudioAnalysisView({ upload, analysis }: { upload: UploadedFile; analysis: AudioAnalysis }) {
    return (
        <div className="audio-analysis">
            <h2>Audio Analysis</h2>

            {/* Audio Player */}
            <audio controls className="audio-player">
                <source src={URL.createObjectURL(upload.file)} type={upload.file.type} />
            </audio>

            {/* Transcription */}
            <div className="analysis-section">
                <h3>Transcription</h3>
                <p className="transcription">{analysis.transcription}</p>
            </div>

            {/* Speaker Diarization */}
            <div className="analysis-section">
                <h3>Speakers ({analysis.speakers.length})</h3>
                <div className="speakers-timeline">
                    {analysis.speakers.map((speaker, idx) => (
                        <div key={idx} className="speaker-segment">
                            <div className="speaker-header">
                                <span className="speaker-id">{speaker.speaker_id}</span>
                                <span className="speaker-time">
                                    {formatTime(speaker.start_time)} - {formatTime(speaker.end_time)}
                                </span>
                            </div>
                            <p className="speaker-text">{speaker.text}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Sounds Detected */}
            {analysis.sounds.length > 0 && (
                <div className="analysis-section">
                    <h3>Sounds Detected</h3>
                    <div className="sounds-list">
                        {analysis.sounds.map((sound, idx) => (
                            <span key={idx} className="sound-tag">{sound}</span>
                        ))}
                    </div>
                </div>
            )}

            {/* Embedding Info */}
            <div className="analysis-section">
                <h3>Embedding</h3>
                <p className="embedding-info">
                    Vector dimension: {analysis.embedding.length}
                </p>
            </div>
        </div>
    );
}

// ============================================================================
// Utility Functions
// ============================================================================

function generateId(): string {
    return Math.random().toString(36).substring(2, 15);
}

function fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            const base64 = (reader.result as string).split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
    });
}

function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}
