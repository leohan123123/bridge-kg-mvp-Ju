import apiClient from '../utils/api.js'; // Assuming api.js exports the configured axios instance

const API_BASE = '/api/v1'; // As per user decision

// General types (can be expanded)
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  // Add other common fields like pagination if necessary
}

// ==== Ontology Management ====

interface OntologyStructure {
  entity_types: Record<string, { properties: string[]; description?: string }>;
  relationship_types: Record<string, { from: string[]; to: string[]; description?: string }>;
}

interface EntityTypePayload {
  entity_type: string;
  properties: string[];
  description?: string;
}

interface OntologySnapshotPayload {
  versionName: string;
  description?: string;
}

interface OntologyVersion {
  name: string;
  timestamp: string;
  description?: string;
}

export const getOntologyStructure = async (): Promise<OntologyStructure> => {
  // The existing OntologyManager.jsx directly expects the data, not wrapped in ApiResponse
  // For now, I'll match that behavior. If backend changes, this should be updated.
  return apiClient.get(`${API_BASE}/ontology/structure`);
};

export const addEntityType = async (payload: EntityTypePayload): Promise<any> => {
  // Existing page expects direct response or error, not wrapped in ApiResponse
  return apiClient.post(`${API_BASE}/ontology/entity_type`, payload);
};

export const createOntologySnapshot = async (payload: OntologySnapshotPayload): Promise<any> => {
  // Existing page expects direct response or error
  return apiClient.post(`${API_BASE}/ontology/snapshot`, payload);
};

export const getOntologyVersions = async (): Promise<OntologyVersion[]> => {
  // Existing page expects a direct array of versions
  return apiClient.get(`${API_BASE}/ontology/versions`);
};

// ==== Batch Processing ====

interface BatchJobCreationPayload {
  file_paths: string[]; // Paths on server after upload
  job_config_str?: string; // JSON string for job configuration
}

interface BatchJobCreationResponse {
  job_id: string;
  message: string;
  // other fields as returned by backend
}

interface BatchJobStatus {
  job_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'PARTIAL_SUCCESS';
  progress?: number; // e.g., 0-100
  total_files?: number;
  processed_files_count?: number;
  successful_files_count?: number;
  failed_files_count?: number;
  estimated_remaining_time_seconds?: number;
  details?: any;
}

interface BatchJobReport {
  job_id: string;
  status: string;
  summary: string;
  results: Array<{ file_path: string; status: 'SUCCESS' | 'FAILURE'; details?: string; output_path?: string }>;
  error_summary?: Array<{file_path: string; reason: string}>;
  // other fields
}

export const createBatchJob = async (payload: FormData): Promise<BatchJobCreationResponse> => {
  // Existing BatchProcessor.jsx uses FormData for this.
  // The backend endpoint /api/v1/batch/process is specified.
  // Note: The existing BatchProcessor.jsx also has an /upload endpoint. This will be handled in the component.
  // This function is for starting the processing of already uploaded files.
  return apiClient.post(`${API_BASE}/batch/process`, payload, {
    headers: {
      // Axios might set this automatically for FormData, but can be explicit if needed
      // 'Content-Type': 'multipart/form-data',
    },
  });
};

export const getBatchJobStatus = async (jobId: string): Promise<BatchJobStatus> => {
  return apiClient.get(`${API_BASE}/batch/status/${jobId}`);
};

export const cancelBatchJob = async (jobId: string): Promise<any> => {
  return apiClient.delete(`${API_BASE}/batch/cancel/${jobId}`);
};

export const getBatchJobReport = async (jobId: string): Promise<BatchJobReport> => {
  return apiClient.get(`${API_BASE}/batch/report/${jobId}`);
};

// ==== Training Data Export ====

interface TrainingDataGeneratePayload {
  type: 'qa' | 'triples' | 'description'; // Example types
  data_amount: number;
  filters?: Record<string, any>; // e.g. { entity_types: [], relation_types: [] }
  quality_params?: Record<string, any>;
}

interface TrainingDataGenerateResponse {
  task_id: string;
  message: string;
  // preview_data?: any[]; // Optional: some preview data
}

interface TrainingDataExportPayload {
  task_id?: string; // If generated from a task
  format: 'JSONL' | 'CSV' | 'RDF' | 'JSON-LD';
  // May also need generation params if not from a task_id
  generation_config?: TrainingDataGeneratePayload;
  custom_template?: string;
  naming_rules?: string;
}

interface TrainingDataExportResponse {
  export_id: string;
  file_url?: string; // URL to download the file
  message: string;
}

interface ExportHistoryItem {
  export_id: string;
  timestamp: string;
  format: string;
  status: 'COMPLETED' | 'FAILED' | 'IN_PROGRESS';
  file_url?: string;
  config_summary: Record<string, any>;
}

interface DataQualityReport {
  report_id: string;
  timestamp: string;
  overall_score: number;
  issues: Array<{issue_type: string; count: number; examples: any[]}>;
  // other fields
}

export const generateTrainingData = async (payload: TrainingDataGeneratePayload): Promise<TrainingDataGenerateResponse> => {
  return apiClient.post(`${API_BASE}/training_data/generate`, payload);
};

export const exportTrainingData = async (payload: TrainingDataExportPayload): Promise<TrainingDataExportResponse> => {
  // Path from instruction: /api/v1/training_data/export
  return apiClient.post(`${API_BASE}/training_data/export`, payload);
};

export const getExportHistory = async (): Promise<ExportHistoryItem[]> => {
  return apiClient.get(`${API_BASE}/training_data/export_history`);
};

export const getDataQualityReport = async (exportId?: string): Promise<DataQualityReport> => {
  // Assuming report might be tied to an exportId or general
  const params = exportId ? { exportId } : {};
  return apiClient.get(`${API_BASE}/training_data/quality_report`, { params }); // Path assumed, needs confirmation
};

// Placeholder types and functions for task status polling (Training Data Export)
export interface TaskStatus {
  task_id: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  progress?: number; // 0-100
  message?: string;
  result_url?: string; // e.g., file_url for export tasks
}

// Mock implementation for getGenerationTaskStatus
let mockGenerationProgress = 0;
let mockGenerationStatus: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' = 'PENDING';
export const getGenerationTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  return new Promise(resolve => {
    setTimeout(() => {
      if (mockGenerationStatus === 'PENDING') {
        mockGenerationStatus = 'PROCESSING';
        mockGenerationProgress = 0;
      } else if (mockGenerationStatus === 'PROCESSING') {
        mockGenerationProgress += 25;
        if (mockGenerationProgress >= 100) {
          mockGenerationStatus = Math.random() > 0.2 ? 'COMPLETED' : 'FAILED'; // 80% chance of success
          mockGenerationProgress = 100;
        }
      }
      resolve({
        task_id: taskId,
        status: mockGenerationStatus,
        progress: mockGenerationProgress,
        message: mockGenerationStatus === 'COMPLETED' ? 'Generation complete.' : (mockGenerationStatus === 'FAILED' ? 'Generation failed.' : 'Processing...'),
      });
      // Reset for next call if task is finished, to allow re-running demo
      if (mockGenerationStatus === 'COMPLETED' || mockGenerationStatus === 'FAILED') {
        mockGenerationStatus = 'PENDING';
        mockGenerationProgress = 0;
      }
    }, 1000);
  });
};

// Mock implementation for getExportTaskStatus
let mockExportProgress = 0;
let mockExportStatus: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' = 'PENDING';
export const getExportTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  return new Promise(resolve => {
    setTimeout(() => {
      if (mockExportStatus === 'PENDING') {
        mockExportStatus = 'PROCESSING';
        mockExportProgress = 0;
      } else if (mockExportStatus === 'PROCESSING') {
        mockExportProgress += 33;
        if (mockExportProgress >= 100) {
          mockExportStatus = Math.random() > 0.15 ? 'COMPLETED' : 'FAILED'; // 85% chance of success
          mockExportProgress = 100;
        }
      }
      resolve({
        task_id: taskId,
        status: mockExportStatus,
        progress: mockExportProgress,
        message: mockExportStatus === 'COMPLETED' ? 'Export complete.' : (mockExportStatus === 'FAILED' ? 'Export failed.' : 'Exporting...'),
        result_url: mockExportStatus === 'COMPLETED' ? `/downloads/export_${taskId}.zip` : undefined,
      });
       // Reset for next call if task is finished
      if (mockExportStatus === 'COMPLETED' || mockExportStatus === 'FAILED') {
        mockExportStatus = 'PENDING';
        mockExportProgress = 0;
      }
    }, 1200);
  });
};


// Note: The actual response structure from apiClient might be { data: YourType }
// if the interceptor `return response.data;` is active.
// The types above are for the expected data *after* the interceptor.
// If the backend wraps responses (e.g., in a `data` field), the calling components might need to adjust,
// or these functions should extract it.
// Given OntologyManager.jsx and BatchProcessor.jsx made direct calls and handled responses,
// these functions currently return the direct response.data for consistency with how existing code might be adapted.
// This matches the behavior of `apiClient.interceptors.response.use(response => response.data)`.
