import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios'; // Assuming axios is used for API calls

// Base URL for the API, adjust if necessary
const API_BASE_URL = '/api/v1'; // Or your full backend URL e.g., http://localhost:8000/api/v1

const BatchProcessor = () => {
    const [selectedFiles, setSelectedFiles] = useState(null);
    const [jobConfig, setJobConfig] = useState('{}'); // Default empty JSON object
    const [uploadResponse, setUploadResponse] = useState(null);
    const [jobId, setJobId] = useState('');
    const [jobStatus, setJobStatus] = useState(null);
    const [jobReport, setJobReport] = useState(null);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [pollingIntervalId, setPollingIntervalId] = useState(null);

    const handleFileChange = (event) => {
        setSelectedFiles(event.target.files);
        setUploadResponse(null); // Reset previous upload info
        setJobId('');
        setJobStatus(null);
        setJobReport(null);
        setError('');
    };

    const handleJobConfigChange = (event) => {
        setJobConfig(event.target.value);
    };

    const handleUpload = async () => {
        if (!selectedFiles || selectedFiles.length === 0) {
            setError('Please select files to upload.');
            return;
        }
        setIsLoading(true);
        setError('');
        setUploadResponse(null);

        const formData = new FormData();
        for (let i = 0; i < selectedFiles.length; i++) {
            formData.append('files', selectedFiles[i]);
        }
        formData.append('job_config_str', jobConfig);

        try {
            const response = await axios.post(`${API_BASE_URL}/batch/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setUploadResponse(response.data);
            setError(response.data.upload_errors ? `Some files had upload issues: ${JSON.stringify(response.data.upload_errors)}` : '');
        } catch (err) {
            setError(`Upload failed: ${err.response?.data?.detail || err.message}`);
            setUploadResponse(null);
        } finally {
            setIsLoading(false);
        }
    };

    const handleStartProcessing = async () => {
        if (!uploadResponse || !uploadResponse.uploaded_file_paths_on_server) {
            setError('Please upload files first or ensure upload was successful.');
            return;
        }
        setIsLoading(true);
        setError('');
        setJobId('');
        setJobStatus(null);
        setJobReport(null);

        const payload = new FormData();
        uploadResponse.uploaded_file_paths_on_server.forEach(path => {
            payload.append('file_paths', path);
        });
        payload.append('job_config_str', JSON.stringify(uploadResponse.job_config_received || {}));


        try {
            // Using FormData for file_paths list as FastAPI handles it well
            const response = await axios.post(`${API_BASE_URL}/batch/process`, payload);
            setJobId(response.data.job_id);
            fetchJobStatus(response.data.job_id); // Initial status fetch
            // Start polling for status
            const intervalId = setInterval(() => fetchJobStatus(response.data.job_id), 5000); // Poll every 5 seconds
            setPollingIntervalId(intervalId);
        } catch (err) {
            setError(`Failed to start processing: ${err.response?.data?.detail || err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchJobStatus = useCallback(async (currentJobId) => {
        if (!currentJobId) return;
        try {
            const response = await axios.get(`${API_BASE_URL}/batch/status/${currentJobId}`);
            setJobStatus(response.data);
            if (response.data.status === 'COMPLETED' || response.data.status === 'FAILED' || response.data.status === 'PARTIAL_SUCCESS' || response.data.status === 'CANCELLED') {
                if (pollingIntervalId) {
                    clearInterval(pollingIntervalId);
                    setPollingIntervalId(null);
                }
                fetchJobReport(currentJobId); // Fetch report once job is done
            }
        } catch (err) {
            setError(`Error fetching job status: ${err.response?.data?.detail || err.message}`);
            if (pollingIntervalId) {
                 clearInterval(pollingIntervalId);
                 setPollingIntervalId(null);
            }
        }
    }, [pollingIntervalId]);


    const fetchJobReport = async (currentJobId) => {
        if (!currentJobId) return;
        setIsLoading(true);
        try {
            const response = await axios.get(`${API_BASE_URL}/batch/report/${currentJobId}`);
            setJobReport(response.data);
        } catch (err) {
            setError(`Error fetching job report: ${err.response?.data?.detail || err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCancelJob = async () => {
        if (!jobId || (jobStatus && ['COMPLETED', 'FAILED', 'CANCELLED'].includes(jobStatus.status)) ) {
            setError('No active job to cancel or job already finished.');
            return;
        }
        setIsLoading(true);
        try {
            await axios.delete(`${API_BASE_URL}/batch/cancel/${jobId}`);
            // Status will be updated by the poller, or force a fetch
            fetchJobStatus(jobId);
        } catch (err) {
             setError(`Error cancelling job: ${err.response?.data?.detail || err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Cleanup polling on component unmount
    useEffect(() => {
        return () => {
            if (pollingIntervalId) {
                clearInterval(pollingIntervalId);
            }
        };
    }, [pollingIntervalId]);

    // Helper to download report data as JSON
    const downloadReport = () => {
        if (!jobReport) return;
        const jsonString = `data:text/json;charset=utf-f8,${encodeURIComponent(
            JSON.stringify(jobReport, null, 2) // Pretty print JSON
        )}`;
        const link = document.createElement("a");
        link.href = jsonString;
        link.download = `batch_report_${jobId}.json`;
        link.click();
    };


    return (
        <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
            <h1>Batch Document Processor</h1>

            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
            {isLoading && <p>Loading...</p>}

            {/* 1. File Selection and Upload */}
            <section style={{ marginBottom: '30px', border: '1px solid #ccc', padding: '15px' }}>
                <h2>1. Upload Files</h2>
                <div>
                    <input type="file" multiple onChange={handleFileChange} disabled={isLoading} />
                </div>
                <div style={{ marginTop: '10px' }}>
                    <label htmlFor="jobConfig">Job Configuration (JSON):</label>
                    <textarea
                        id="jobConfig"
                        value={jobConfig}
                        onChange={handleJobConfigChange}
                        rows="3"
                        style={{ width: '100%', boxSizing: 'border-box' }}
                        placeholder='e.g., {"mode": "full_analysis", "priority": "high"}'
                        disabled={isLoading}
                    />
                </div>
                <button onClick={handleUpload} disabled={isLoading || !selectedFiles}>
                    Upload Selected Files
                </button>
                {uploadResponse && (
                    <div style={{ marginTop: '10px', backgroundColor: '#f0f0f0', padding: '10px' }}>
                        <h4>Upload Result:</h4>
                        <p>{uploadResponse.message}</p>
                        {uploadResponse.batch_upload_id && <p>Batch Upload ID: {uploadResponse.batch_upload_id}</p>}
                        {uploadResponse.uploaded_file_paths_on_server && (
                            <p>Files prepared on server: {uploadResponse.uploaded_file_paths_on_server.length}</p>
                        )}
                         {uploadResponse.upload_errors && (
                            <div><strong>Upload Errors:</strong> <pre>{JSON.stringify(uploadResponse.upload_errors, null, 2)}</pre></div>
                        )}
                    </div>
                )}
            </section>

            {/* 2. Start Processing */}
            {uploadResponse && uploadResponse.uploaded_file_paths_on_server?.length > 0 && (
                <section style={{ marginBottom: '30px', border: '1px solid #ccc', padding: '15px' }}>
                    <h2>2. Start Processing</h2>
                    <button onClick={handleStartProcessing} disabled={isLoading || jobId !== ''}>
                        Start Processing Uploaded Batch
                    </button>
                    {jobId && <p>Processing Job ID: <strong>{jobId}</strong></p>}
                </section>
            )}

            {/* 3. Progress Monitoring and Status */}
            {jobId && (
                <section style={{ marginBottom: '30px', border: '1px solid #ccc', padding: '15px' }}>
                    <h2>3. Job Status & Progress</h2>
                    {jobStatus ? (
                        <div>
                            <p><strong>Status:</strong> {jobStatus.status}</p>
                            <p>Total Files: {jobStatus.total_files}</p>
                            <p>Processed: {jobStatus.processed_files_count}</p>
                            <p>Successful: {jobStatus.successful_files_count}</p>
                            <p>Failed: {jobStatus.failed_files_count}</p>
                            <p>Est. Remaining Time: {jobStatus.estimated_remaining_time_seconds} seconds</p>
                            {jobStatus.status === 'RUNNING' &&
                                <progress value={jobStatus.processed_files_count} max={jobStatus.total_files} style={{width: "100%"}}/>
                            }
                        </div>
                    ) : <p>Fetching status...</p>}
                    {jobStatus && jobStatus.status === 'RUNNING' && (
                         <button onClick={handleCancelJob} disabled={isLoading} style={{marginTop: "10px", backgroundColor: "orange"}}>
                            Cancel Job
                        </button>
                    )}
                </section>
            )}

            {/* 4. Error Files List & Retry (Placeholder) */}
            {jobStatus && jobStatus.failed_files_count > 0 && jobReport && jobReport.error_summary && (
                 <section style={{ marginBottom: '30px', border: '1px solid #ccc', padding: '15px' }}>
                    <h2>4. Failed Files</h2>
                    <p>Number of files failed: {jobStatus.failed_files_count}</p>
                    <ul>
                        {jobReport.error_summary.map((err, index) => (
                            <li key={index}>
                                File: {err.file_path || 'N/A'} - Reason: {err.reason || 'Unknown'}
                            </li>
                        ))}
                    </ul>
                    {/* <button disabled>Retry Failed Files (Not Implemented)</button> */}
                 </section>
            )}


            {/* 5. Batch Report and Download */}
            {jobReport && (
                <section style={{ border: '1px solid #ccc', padding: '15px' }}>
                    <h2>5. Batch Processing Report</h2>
                    <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', backgroundColor: '#eee', padding: '10px' }}>
                        {JSON.stringify(jobReport, null, 2)}
                    </pre>
                    <button onClick={downloadReport}>Download Report as JSON</button>
                </section>
            )}
        </div>
    );
};

export default BatchProcessor;
