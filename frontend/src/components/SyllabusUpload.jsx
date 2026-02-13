import { useState, useRef } from 'react';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { ProgressBar } from 'primereact/progressbar';
import { Card } from 'primereact/card';
import { FileUpload } from 'primereact/fileupload';
import { Badge } from 'primereact/badge';
import { Divider } from 'primereact/divider';
import { Dialog } from 'primereact/dialog';
import apiClient from '../api/api';
import './SyllabusUpload.css';

export default function SyllabusUpload() {
  const toastRef = useRef(null);
  const fileUploadRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedSyllabuses, setUploadedSyllabuses] = useState([]);
  const [showUploadedList, setShowUploadedList] = useState(false);
  const [selectedSyllabus, setSelectedSyllabus] = useState(null);
  const [showHierarchyDialog, setShowHierarchyDialog] = useState(false);

  const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.csv'];
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

  const handleUpload = async (event) => {
    const file = event.files[0];
    if (!file) return;

    if (!validateFile(file)) {
      fileUploadRef.current?.clear();
      return;
    }

    setIsLoading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('token');

      const response = await apiClient.post('/syllabus/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${token}`,
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(percentCompleted);
        },
      });

      if (response.data.success) {
        toastRef.current?.show({
          severity: 'success',
          summary: 'Upload Successful',
          detail: `Syllabus "${file.name}" uploaded and analyzed!`,
          life: 4000,
        });

        setUploadedSyllabuses((prev) => [
          response.data.data,
          ...prev,
        ]);

        fileUploadRef.current?.clear();
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
      setUploadProgress(0);
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

  const handleDeleteSyllabus = async (syllabusId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await apiClient.delete(`/syllabus/${syllabusId}`, {
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
        setUploadedSyllabuses((prev) => prev.filter((s) => s.id !== syllabusId));
      }
    } catch (error) {
      console.error('Delete error:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to delete syllabus',
        life: 4000,
      });
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
          Upload a syllabus document (PDF, DOCX, or CSV) for AI-powered analysis.
          The system will automatically extract course units, topics, and key concepts.
        </p>

        <div className="upload-area">
          <FileUpload
            ref={fileUploadRef}
            name="file"
            accept=".pdf,.docx,.csv"
            maxFileSize={MAX_FILE_SIZE}
            customUpload
            uploadHandler={handleUpload}
            auto={false}
            chooseLabel="Choose File"
            uploadLabel="Upload"
            cancelLabel="Clear"
            showUploadButton
            showCancelButton
            disabled={isLoading}
            className="file-upload-widget"
            headerTemplate={
              <div className="upload-header">
                <i className="pi pi-cloud-upload upload-icon"></i>
                <span>Select a file to upload</span>
              </div>
            }
          />
        </div>

        {isLoading && (
          <div className="progress-container">
            <p>🔄 Uploading and analyzing... {uploadProgress}%</p>
            <ProgressBar value={uploadProgress} showValue={false} />
          </div>
        )}

        <div className="file-info">
          <Badge value="PDF" icon="pi pi-file-pdf" severity="danger"></Badge>
          <Badge value="DOCX" icon="pi pi-file-word" severity="info"></Badge>
          <Badge value="CSV" icon="pi pi-file" severity="warning"></Badge>
          <p><strong>Maximum file size:</strong> 50 MB</p>
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
            {uploadedSyllabuses.map((syllabus) => (
              <Card key={syllabus.id} className="syllabus-card">
                <div className="syllabus-header">
                  <div className="syllabus-info">
                    <h4>{syllabus.course_name || syllabus.filename}</h4>
                    <p className="file-type">
                      <i className={`pi pi-${
                        syllabus.file_type === 'pdf' ? 'file-pdf' :
                        syllabus.file_type === 'docx' ? 'file-word' :
                        'file'
                      }`}></i>
                      {syllabus.file_type.toUpperCase()}
                    </p>
                  </div>
                  <div className="action-buttons">
                    <Button
                      icon="pi pi-fw pi-eye"
                      className="p-button-rounded p-button-success p-button-text"
                      onClick={() => viewHierarchy(syllabus)}
                      tooltip="View Hierarchy"
                      disabled={!syllabus.hierarchy}
                    />
                    <Button
                      icon="pi pi-fw pi-trash"
                      className="p-button-rounded p-button-danger p-button-text"
                      onClick={() => handleDeleteSyllabus(syllabus.id)}
                      tooltip="Delete"
                    />
                  </div>
                </div>

                <Divider />

                <div className="syllabus-stats">
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
                      {(syllabus.file_size_bytes / 1024).toFixed(2)} KB
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
    </div>
  );
}
