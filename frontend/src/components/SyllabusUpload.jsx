import { useState, useRef } from 'react';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { ProgressBar } from 'primereact/progressbar';
import { Card } from 'primereact/card';
import { FileUpload } from 'primereact/fileupload';
import { Badge } from 'primereact/badge';
import { Divider } from 'primereact/divider';
import { Dialog } from 'primereact/dialog';
import { Dropdown } from 'primereact/dropdown';
import apiClient from '../api/api';
import './SyllabusUpload.css';

export default function SyllabusUpload() {
  const toastRef = useRef(null);
  const fileUploadRef = useRef(null);
  const nativeFileInputRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedSyllabuses, setUploadedSyllabuses] = useState([]);
  const [showUploadedList, setShowUploadedList] = useState(false);
  const [selectedSyllabus, setSelectedSyllabus] = useState(null);
  const [showHierarchyDialog, setShowHierarchyDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [analyzeProgress, setAnalyzeProgress] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeResult, setAnalyzeResult] = useState(null);
  const [uploadedSyllabusId, setUploadedSyllabusId] = useState(null);
  const [uploadedSyllabusData, setUploadedSyllabusData] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState('');
  const [selectedDepartment, setSelectedDepartment] = useState('CSE');
  const [deleteSyllabusData, setDeleteSyllabusData] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Department options
  const departmentOptions = [
    { label: 'Computer Science & Engineering (CSE)', value: 'CSE' },
    { label: 'Information Technology (IT)', value: 'IT' },
    { label: 'Electronics & Communication (ECE)', value: 'ECE' },
    { label: 'Electrical & Electronics (EEE)', value: 'EEE' },
    { label: 'Mechanical (MECH)', value: 'MECH' },
    { label: 'Civil (CIVIL)', value: 'CIVIL' }
  ];
  const handleAnalyzeClick = async () => {
    if (!uploadedSyllabusId) {
      toastRef.current?.show({
        severity: 'warn',
        summary: 'No Syllabus Uploaded',
        detail: 'Please upload a syllabus before analyzing',
        life: 3000,
      });
      return;
    }
    setIsAnalyzing(true);
    setAnalyzeProgress(0);
    setAnalyzeResult(null);
    
    let progress = 0;
    let timer = null;
    
    const incrementProgress = () => {
      progress += Math.random() * 12 + 4; // increment by 4-16%
      if (progress < 90) {
        setAnalyzeProgress(Math.floor(progress));
        timer = setTimeout(incrementProgress, 350);
      }
    };
    
    incrementProgress();
    
    try {
      const token = localStorage.getItem('token');
      const response = await apiClient.post(
        `/syllabus/${uploadedSyllabusId}/analyze`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setAnalyzeProgress(100);
      
      if (response.data.success) {
        setAnalyzeResult(response.data.data);
        toastRef.current?.show({
          severity: 'success',
          summary: '✓ Analysis Complete',
          detail: 'Syllabus analyzed successfully!',
          life: 4000,
        });
        setUploadedSyllabusData((prev) => ({ ...prev, ...response.data.data }));
        fetchSyllabuses();
      } else {
        toastRef.current?.show({
          severity: 'error',
          summary: 'Analysis Failed',
          detail: response.data.message || 'Failed to analyze syllabus',
          life: 4000,
        });
      }
    } catch (error) {
      toastRef.current?.show({
        severity: 'error',
        summary: 'Analysis Error',
        detail: error.response?.data?.detail || error.message || 'Failed to analyze syllabus',
        life: 4000,
      });
    } finally {
      setIsAnalyzing(false);
      if (timer) clearTimeout(timer);
    }
  };

  const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.csv', '.txt'];
  const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

  const validateFile = (file) => {
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(fileExtension)) {
      toastRef.current?.show({
        severity: 'error',
        summary: 'Invalid File Type',
        detail: `Only PDF, DOCX, and CSV files are allowed. Got ${fileExtension}`,
        life: 4000,
      });
      return false;
    }
    if (file.size > MAX_FILE_SIZE) {
      toastRef.current?.show({
        severity: 'error',
        summary: 'File Too Large',
        detail: `File size exceeds 50MB limit. File size: ${(file.size / 1024 / 1024).toFixed(2)}MB`,
        life: 4000,
      });
      return false;
    }
    return true;
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!validateFile(file)) {
      return;
    }
    setSelectedFile(file);
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUploadClick = async () => {
    if (!selectedFile) {
      toastRef.current?.show({
        severity: 'warn',
        summary: 'No File Selected',
        detail: 'Please select a file before uploading',
        life: 3000,
      });
      return;
    }
    setIsLoading(true);
    setUploadProgress(0);
    setUploadSuccess(false);
    
    let progress = 0;
    let timer = null;
    
    const incrementProgress = () => {
      progress += Math.random() * 15 + 5; // increment by 5-20%
      if (progress < 90) {
        setUploadProgress(Math.floor(progress));
        timer = setTimeout(incrementProgress, 300);
      }
    };
    
    incrementProgress();
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('department', selectedDepartment);
      const token = localStorage.getItem('token');
      
      // Show info message about processing time
      toastRef.current?.show({
        severity: 'info',
        summary: '⏳ Uploading Syllabus',
        detail: 'Uploading your syllabus file (this may take a few moments)...',
        life: 0,
        sticky: true
      });
      
      const response = await apiClient.post('/syllabus/upload', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // Remove the processing message
      toastRef.current?.clear();
      
      // Complete the progress bar
      setUploadProgress(100);
      
      if (response.data.success) {
        setUploadedSyllabusId(response.data.data.syllabus_id);
        setUploadedSyllabusData(response.data.data);
        setUploadSuccess(true);
        setUploadSuccessMessage(response.data.message || 'Upload successful!');
        
        // Fetch updated syllabus list only after successful upload
        await fetchSyllabuses();
        
        // Show toast notification
        if (response.data.message && response.data.message.includes('same content')) {
          toastRef.current?.show({
            severity: 'warn',
            summary: '⚠️ Duplicate Content Detected',
            detail: response.data.message,
            life: 5000,
          });
        } else {
          toastRef.current?.show({
            severity: 'success',
            summary: '✓ Upload Successful',
            detail: 'File uploaded successfully!',
            life: 3000,
          });
        }
      } else {
        toastRef.current?.show({
          severity: 'error',
          summary: 'Upload Failed',
          detail: response.data.message || 'Failed to upload syllabus',
          life: 4000,
        });
      }
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage =
        error.response?.data?.detail || error.message || 'Failed to upload syllabus';
      toastRef.current?.show({
        severity: 'error',
        summary: 'Upload Error',
        detail: errorMessage,
        life: 4000,
      });
    } finally {
      setIsLoading(false);
      if (timer) clearTimeout(timer);
    }
  };

  const fetchSyllabuses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await apiClient.get('/syllabus/list', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.data.success) {
        setUploadedSyllabuses(response.data.data);
        setShowUploadedList(true);
      }
    } catch (error) {
      console.error('Fetch error:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to fetch uploaded syllabuses',
        life: 4000,
      });
    }
  };

  const handleDeleteSyllabus = (syllabusId) => {
    setDeleteSyllabusData(syllabusId);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteSyllabus = async () => {
    if (!deleteSyllabusData) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await apiClient.delete(`/syllabus/${deleteSyllabusData}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.data.success) {
        toastRef.current?.show({
          severity: 'success',
          summary: 'Deleted',
          detail: 'Syllabus deleted successfully',
          life: 4000,
        });
        setUploadedSyllabuses((prev) => prev.filter((s) => s.id !== deleteSyllabusData));
        
        // Notify UnitConceptSelector to refresh via localStorage event
        localStorage.setItem('syllabusDeleted', JSON.stringify({ syllabusId: deleteSyllabusData, timestamp: Date.now() }));
        
        // Close the confirmation dialog
        setShowDeleteConfirm(false);
        setDeleteSyllabusData(null);
      }
    } catch (error) {
      console.error('Delete error:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to delete syllabus',
        life: 4000,
      });
      setShowDeleteConfirm(false);
      setDeleteSyllabusData(null);
    }
  };

  const viewHierarchy = (syllabus) => {
    setSelectedSyllabus(syllabus);
    setShowHierarchyDialog(true);
  };

  const HierarchyView = ({ hierarchy }) => {
    if (!hierarchy || !hierarchy.units) return <p>No hierarchy data available</p>;

    return (
      <div className="hierarchy-view">
        {hierarchy.units.map((unit, unitIdx) => (
          <div key={unitIdx} className="unit-section">
            <div className="unit-header">
              <i className="pi pi-fw pi-folder"></i>
              <h4>{unit.unit_name}</h4>
              <Badge value={unit.topics?.length || 0} className="ml-2"></Badge>
            </div>
            {unit.description && <p className="unit-description">{unit.description}</p>}
            
            {unit.topics && unit.topics.length > 0 && (
              <div className="topics-container">
                {unit.topics.map((topic, topicIdx) => (
                  <div key={topicIdx} className="topic-item">
                    <div className="topic-header">
                      <i className="pi pi-fw pi-book"></i>
                      <span className="topic-name">{topic.topic_name}</span>
                      <Badge value={topic.concepts?.length || 0} severity="info"></Badge>
                    </div>
                    {topic.concepts && topic.concepts.length > 0 && (
                      <div className="concepts-list">
                        {topic.concepts.map((concept, conceptIdx) => (
                          <div key={conceptIdx} className="concept-tag">
                            <i className="pi pi-fw pi-check-circle"></i>
                            <span>{concept}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="syllabus-upload-container">
      <Toast ref={toastRef} position="top-right" />

      {/* Hierarchy Dialog */}
      <Dialog
        header={selectedSyllabus?.course_name || 'Course Hierarchy'}
        visible={showHierarchyDialog}
        onHide={() => setShowHierarchyDialog(false)}
        style={{ width: '90vw', maxWidth: '900px' }}
        modal
      >
        {selectedSyllabus && <HierarchyView hierarchy={selectedSyllabus.hierarchy} />}
      </Dialog>

      <Card className="upload-card">
        <h3>📚 Upload Course Syllabus</h3>
        <p className="upload-description">
          Upload a syllabus document (PDF, DOCX, CSV, or TXT) for AI-powered analysis.
          The system will automatically extract course units, topics, and key concepts.
        </p>

        <div className="department-selection" style={{ marginBottom: '1.5rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            📋 Select Department
          </label>
          <Dropdown
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.value)}
            options={departmentOptions}
            placeholder="Select a department"
            style={{ width: '100%' }}
          />
        </div>

        <div className="upload-area" style={{ position: 'relative' }}>
          {!selectedFile ? (
            <div className="upload-drag-drop-wrapper">
              <div className="upload-drag-drop-area">
                <i className="pi pi-cloud-upload upload-icon-large"></i>
                <h4>Drag and Drop Your Syllabus Here</h4>
                <p className="or-text">OR</p>
                <Button
                  label="📁 Click Here to Browse Files"
                  icon="pi pi-fw pi-folder-open"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (nativeFileInputRef.current) {
                      nativeFileInputRef.current.value = '';
                      nativeFileInputRef.current.click();
                    }
                  }}
                  className="p-button-secondary browse-btn"
                  disabled={isLoading}
                />
                <input
                  ref={nativeFileInputRef}
                  type="file"
                  accept=".pdf,.docx,.csv,.txt"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const file = e.target.files && e.target.files[0];
                    if (file) handleFileSelect(file);
                  }}
                  tabIndex={-1}
                  aria-hidden="true"
                />
              </div>
            </div>
          ) : isLoading ? (
            <div className="upload-progress-section">
              <div className="progress-content">
                <p className="progress-title">
                  📤 Uploading the syllabus...
                </p>
                <ProgressBar value={uploadProgress} showValue={true} />
                <p className="progress-subtitle">Please wait while your file is being uploaded</p>
              </div>
            </div>
          ) : uploadSuccess ? (
            <div className="upload-success-section">
              <div className="success-message">
                <i className="pi pi-check-circle success-icon"></i>
                <h4>✓ Upload Successful</h4>
                <p className="message-detail">{uploadSuccessMessage}</p>
              </div>
              
              <Divider />
              
              <div className="uploaded-file-info">
                <div className="file-info-header">
                  <i className={`pi pi-${
                    uploadedSyllabusData?.file_type === 'pdf' ? 'file-pdf' :
                    uploadedSyllabusData?.file_type === 'docx' ? 'file-word' :
                    uploadedSyllabusData?.file_type === 'csv' ? 'file' :
                    'file'
                  }`} style={{ fontSize: '2rem', color: '#667eea', marginRight: '1rem' }}></i>
                  <div>
                    <p className="filename">{uploadedSyllabusData?.filename}</p>
                    <p className="file-meta">{(uploadedSyllabusData?.file_size_bytes / 1024).toFixed(2)} KB</p>
                  </div>
                </div>
              </div>
              
              {isAnalyzing ? (
                <div className="analyze-progress-section" style={{ marginTop: '1.5rem' }}>
                  <p className="progress-title">🧠 Analysing the syllabus...</p>
                  <ProgressBar value={analyzeProgress} showValue={true} />
                  <p className="progress-subtitle">Extracting units, topics, and concepts from your syllabus (this may take a minute or two)</p>
                </div>
              ) : analyzeResult ? (
                <div className="analyze-success-section" style={{ marginTop: '1.5rem' }}>
                  <div className="success-badge">
                    <i className="pi pi-check-circle" style={{ marginRight: '0.5rem' }}></i>
                    Analysis Complete!
                  </div>
                  <div className="analysis-summary" style={{ marginTop: '1rem' }}>
                    <div className="summary-item">
                      <i className="pi pi-folder" style={{ marginRight: '0.5rem' }}></i>
                      <span><strong>Units:</strong> {uploadedSyllabusData?.analysis_summary?.total_units || 0}</span>
                    </div>
                    <div className="summary-item">
                      <i className="pi pi-book" style={{ marginRight: '0.5rem' }}></i>
                      <span><strong>Topics:</strong> {uploadedSyllabusData?.analysis_summary?.total_topics || 0}</span>
                    </div>
                    <div className="summary-item">
                      <i className="pi pi-check-circle" style={{ marginRight: '0.5rem' }}></i>
                      <span><strong>Concepts:</strong> {uploadedSyllabusData?.analysis_summary?.total_concepts || 0}</span>
                    </div>
                  </div>
                  <div className="action-buttons" style={{ marginTop: '1.5rem' }}>
                    <Button
                      label="Clear"
                      icon="pi pi-fw pi-trash"
                      onClick={() => {
                        setSelectedFile(null);
                        setUploadSuccess(false);
                        setUploadedSyllabusId(null);
                        setUploadedSyllabusData(null);
                        setAnalyzeResult(null);
                        setUploadSuccessMessage('');
                        if (nativeFileInputRef.current) nativeFileInputRef.current.value = '';
                      }}
                      className="p-button-secondary clear-btn"
                      severity="secondary"
                    />
                  </div>
                </div>
              ) : (
                <div className="action-buttons" style={{ marginTop: '1.5rem' }}>
                  <Button
                    label="🧠 Analyze Syllabus"
                    icon="pi pi-fw pi-search"
                    onClick={handleAnalyzeClick}
                    className="p-button-info analyze-btn"
                    disabled={isAnalyzing}
                    loading={isAnalyzing}
                    size="large"
                  />
                  <Button
                    label="Upload Different File"
                    icon="pi pi-fw pi-times"
                    onClick={() => {
                      setSelectedFile(null);
                      setUploadSuccess(false);
                      setUploadedSyllabusId(null);
                      setUploadedSyllabusData(null);
                      setAnalyzeResult(null);
                      if (nativeFileInputRef.current) nativeFileInputRef.current.value = '';
                    }}
                    className="p-button-secondary"
                    disabled={isAnalyzing}
                    severity="secondary"
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="file-selected-section">
              <div className="selected-file-display">
                <i className="pi pi-fw pi-file-pdf file-icon" style={{ color: '#ff5252' }}></i>
                <div className="file-details">
                  <p className="selected-filename">✓ {selectedFile.name}</p>
                  <p className="selected-filesize">({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)</p>
                </div>
              </div>
              <div className="upload-action-buttons">
                <Button
                  label="📤 Upload Syllabus"
                  icon="pi pi-fw pi-upload"
                  onClick={handleUploadClick}
                  className="p-button-success upload-btn"
                  disabled={isLoading || isAnalyzing}
                  loading={isLoading}
                  size="large"
                />
                <Button
                  label="Choose Different File"
                  icon="pi pi-fw pi-times"
                  onClick={() => {
                    setSelectedFile(null);
                    if (nativeFileInputRef.current) nativeFileInputRef.current.value = '';
                  }}
                  className="p-button-secondary"
                  disabled={isLoading || isAnalyzing}
                  severity="secondary"
                />
              </div>
            </div>
          )}
        </div>
      </Card>

      <Button
        label="View Uploaded Syllabuses"
        icon="pi pi-fw pi-list"
        onClick={fetchSyllabuses}
        className="p-button-info view-button"
        disabled={isLoading}
      />

      {showUploadedList && uploadedSyllabuses.length > 0 && (
        <div className="syllabuses-list">
          <h3>📖 Uploaded Syllabuses ({uploadedSyllabuses.length})</h3>
          <div className="syllabuses-grid">
            {[...uploadedSyllabuses]
              .sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at))
              .map((syllabus) => (
              <Card key={syllabus.id} className="syllabus-card">
                <div className="syllabus-header">
                  <div className="syllabus-info">
                    <h4>
                      <i className={`pi pi-${
                        syllabus.file_type === 'pdf' ? 'file-pdf' :
                        syllabus.file_type === 'docx' ? 'file-word' :
                        syllabus.file_type === 'csv' ? 'file' :
                        'file'
                      }`} style={{ marginRight: '8px' }}></i>
                      {syllabus.filename}
                    </h4>
                  </div>
                  <div className="action-buttons">
                    <Button
                      icon="pi pi-fw pi-eye"
                      className="p-button-rounded p-button-success p-button-text"
                      onClick={() => viewHierarchy(syllabus)}
                      tooltip="View Hierarchy"
                      tooltipPosition="bottom"
                      disabled={!syllabus.hierarchy}
                    />
                    <Button
                      icon="pi pi-fw pi-trash"
                      className="p-button-rounded p-button-danger p-button-text"
                      onClick={() => handleDeleteSyllabus(syllabus.id)}
                      tooltip="Delete"
                      tooltipPosition="bottom"
                    />
                  </div>
                </div>

                <Divider />

                <div className="syllabus-stats stat-row">
                  <div className="stat-item">
                    <i className="pi pi-folder"></i>
                    <div>
                      <span className="stat-label">Units</span>
                      <span className="stat-value">{syllabus.analysis_summary?.total_units || 0}</span>
                    </div>
                  </div>
                  <div className="stat-item">
                    <i className="pi pi-book"></i>
                    <div>
                      <span className="stat-label">Topics</span>
                      <span className="stat-value">{syllabus.analysis_summary?.total_topics || 0}</span>
                    </div>
                  </div>
                  <div className="stat-item">
                    <i className="pi pi-check-circle"></i>
                    <div>
                      <span className="stat-label">Concepts</span>
                      <span className="stat-value">{syllabus.analysis_summary?.total_concepts || 0}</span>
                    </div>
                  </div>
                </div>

                <Divider />

                <div className="syllabus-details">
                  <div className="detail-item">
                    <span className="label">Department:</span>
                    <span className="value">{syllabus.department}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Size:</span>
                    <span className="value">
                      {syllabus.file_size_bytes ? (syllabus.file_size_bytes / 1024).toFixed(2) : '0'} KB
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Uploaded:</span>
                    <span className="value">
                      {new Date(syllabus.uploaded_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {showUploadedList && uploadedSyllabuses.length === 0 && (
        <Card className="empty-state">
          <i className="pi pi-inbox empty-icon"></i>
          <p>No syllabuses uploaded yet. Upload your first syllabus to get started!</p>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        visible={showDeleteConfirm}
        onHide={() => setShowDeleteConfirm(false)}
        header="Confirm Delete"
        modal
        footer={
          <div>
            <Button 
              label="Cancel" 
              onClick={() => setShowDeleteConfirm(false)} 
              className="p-button-secondary"
            />
            <Button 
              label="Delete" 
              onClick={confirmDeleteSyllabus} 
              className="p-button-danger"
            />
          </div>
        }
      >
        <p>
          Are you sure you want to delete this syllabus? This action cannot be undone and will remove all associated tasks and progress data.
        </p>
      </Dialog>
    </div>
  );
}
