import { useState, useEffect, useRef } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { Tag } from 'primereact/tag';
import { Dialog } from 'primereact/dialog';
import { InputTextarea } from 'primereact/inputtextarea';
import { InputNumber } from 'primereact/inputnumber';
import { Calendar } from 'primereact/calendar';
import './TasksList.css';

export default function TasksList() {
  const toastRef = useRef(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskDialog, setTaskDialog] = useState(false);
  const [progressDialog, setProgressDialog] = useState(false);
  const [globalFilter, setGlobalFilter] = useState('');
  const [updatingProgress, setUpdatingProgress] = useState(false);
  const [progressData, setProgressData] = useState({
    status: 'IN_PROGRESS',
    completion_percentage: 0,
    start_date: null,
    end_date: null,
    covered_topics: [],
    notes: ''
  });

  // Fetch tasks on component mount
  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const userId = JSON.parse(localStorage.getItem('user'))?.id;

      const response = await fetch(
        `http://localhost:8000/tasks?staff_id=${userId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch tasks');
      }

      const result = await response.json();
      if (result.success && result.data) {
        setTasks(result.data);
      }
    } catch (error) {
      console.error('Error fetching tasks:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load tasks',
        life: 3000
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusSeverity = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'success';
      case 'IN_PROGRESS':
        return 'info';
      case 'PENDING':
        return 'warning';
      case 'OVERDUE':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  const getTypeSeverity = (type) => {
    switch (type) {
      case 'QUIZ':
        return 'info';
      case 'ASSIGNMENT':
        return 'warning';
      case 'PROJECT':
        return 'danger';
      case 'READING':
        return 'secondary';
      case 'PROBLEM_SOLVING':
        return 'success';
      case 'DISCUSSION':
        return 'primary';
      default:
        return 'secondary';
    }
  };

  const statusTemplate = (rowData) => (
    <Tag 
      value={rowData.status?.replace('_', ' ') || 'PENDING'} 
      severity={getStatusSeverity(rowData.status)}
      style={{ fontSize: '12px', fontWeight: '600' }}
    />
  );

  const typeTemplate = (rowData) => (
    <Tag 
      value={rowData.task_type?.replace('_', ' ') || 'TASK'} 
      severity={getTypeSeverity(rowData.task_type)}
      style={{ fontSize: '12px', fontWeight: '600' }}
    />
  );

  const actionTemplate = (rowData) => (
    <div className="action-buttons">
      <Button
        icon="pi pi-eye"
        rounded
        className="p-button-sm p-button-info"
        onClick={() => {
          setSelectedTask(rowData);
          setTaskDialog(true);
        }}
        tooltip="View Details"
        tooltipPosition="bottom"
      />
      {rowData.status !== 'COMPLETED' && (
        <Button
          icon="pi pi-edit"
          rounded
          className="p-button-sm p-button-warning"
          onClick={() => {
            setSelectedTask(rowData);
            setProgressData({
              status: rowData.status || 'IN_PROGRESS',
              completion_percentage: rowData.completion_percentage || 0,
              start_date: rowData.start_date ? new Date(rowData.start_date) : null,
              end_date: rowData.end_date ? new Date(rowData.end_date) : null,
              covered_topics: rowData.covered_topics || [],
              notes: rowData.notes || ''
            });
            setProgressDialog(true);
          }}
          tooltip="Update Progress"
          tooltipPosition="bottom"
        />
      )}
    </div>
  );

  const dateTemplate = (rowData, field) => {
    if (!rowData[field]) return '-';
    return new Date(rowData[field]).toLocaleDateString();
  };

  const effortTemplate = (rowData) => {
    if (!rowData.effort_hours) return '-';
    return `${rowData.effort_hours}h`;
  };

  const complexityTemplate = (rowData) => {
    if (!rowData.average_complexity) return '-';
    const severity = rowData.average_complexity === 'LOW' ? 'success' : 
                     rowData.average_complexity === 'MEDIUM' ? 'warning' : 'danger';
    return (
      <Tag 
        value={rowData.average_complexity} 
        severity={severity}
        style={{ fontSize: '11px', fontWeight: '600' }}
      />
    );
  };

  const completionTemplate = (rowData) => {
    return (
      <div className="completion-bar">
        <div className="progress-bar" style={{ width: `${rowData.completion_percentage || 0}%` }}></div>
        <span className="completion-text">{rowData.completion_percentage || 0}%</span>
      </div>
    );
  };

  const handleUpdateProgress = async () => {
    try {
      setUpdatingProgress(true);
      const token = localStorage.getItem('token');
      
      const updatePayload = {
        status: progressData.status,
        completion_percentage: progressData.completion_percentage,
        start_date: progressData.start_date?.toISOString(),
        end_date: progressData.end_date?.toISOString(),
        covered_topics: progressData.covered_topics,
        notes: progressData.notes
      };

      const response = await fetch(`http://localhost:8000/tasks/${selectedTask.id}/progress`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updatePayload)
      });

      if (!response.ok) {
        throw new Error('Failed to update task progress');
      }

      const result = await response.json();
      
      if (result.success) {
        toastRef.current?.show({
          severity: 'success',
          summary: '✓ Progress Updated',
          detail: 'Task progress updated successfully',
          life: 3000
        });
        setProgressDialog(false);
        fetchTasks(); // Refresh tasks list
      } else {
        throw new Error(result.message || 'Failed to update task progress');
      }
    } catch (error) {
      console.error('Error updating progress:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.message || 'Failed to update task progress',
        life: 3000
      });
    } finally {
      setUpdatingProgress(false);
    }
  };

  return (
    <div className="tasks-list-container">
      <Toast ref={toastRef} position="top-right" />

      <Card className="tasks-card">
        <div className="tasks-header">
          <h3>📋 All Assigned Tasks</h3>
          <div className="tasks-actions">
            <span className="task-count-badge">{tasks.length} tasks</span>
            <Button
              icon="pi pi-refresh"
              className="p-button-rounded p-button-secondary"
              onClick={fetchTasks}
              loading={loading}
              tooltip="Refresh"
              tooltipPosition="bottom"
            />
          </div>
        </div>

        {tasks.length > 0 ? (
          <DataTable
            value={tasks}
            loading={loading}
            globalFilter={globalFilter}
            paginator
            rows={10}
            dataKey="id"
            className="tasks-data-table"
            emptyMessage="No tasks found"
            stripedRows
          >
            <Column field="title" header="Title" sortable filter />
            <Column
              field="task_type"
              header="Type"
              body={typeTemplate}
              sortable
              style={{ width: '100px' }}
            />
            <Column
              field="status"
              header="Status"
              body={statusTemplate}
              sortable
              style={{ width: '100px' }}
            />
            <Column
              field="completion_percentage"
              header="Progress"
              body={completionTemplate}
              style={{ width: '120px' }}
            />
            <Column
              field="effort_hours"
              header="Effort"
              body={effortTemplate}
              sortable
              style={{ width: '80px' }}
            />
            <Column
              field="average_complexity"
              header="Complexity"
              body={complexityTemplate}
              sortable
              style={{ width: '100px' }}
            />
            <Column
              field="start_date"
              header="Start Date"
              body={(rowData) => dateTemplate(rowData, 'start_date')}
              sortable
              style={{ width: '100px' }}
            />
            <Column
              field="end_date"
              header="End Date"
              body={(rowData) => dateTemplate(rowData, 'end_date')}
              sortable
              style={{ width: '100px' }}
            />
            <Column
              header="Action"
              body={actionTemplate}
              style={{ width: '100px', textAlign: 'center' }}
            />
          </DataTable>
        ) : (
          <div className="empty-state">
            <i className="pi pi-inbox" style={{ fontSize: '48px', color: '#9ca3af' }}></i>
            <p>No tasks assigned yet</p>
            <small>Tasks will appear here once you assign concepts for learning</small>
          </div>
        )}
      </Card>

      {/* Task Details Dialog */}
      <Dialog
        visible={taskDialog}
        onHide={() => setTaskDialog(false)}
        header={selectedTask?.title}
        modal
        style={{ width: '90vw', maxWidth: '600px' }}
        className="task-details-dialog"
      >
        {selectedTask && (
          <div className="task-details">
            <di className="detail-section">
              <h5>Task Information</h5>
              <div className="detail-item">
                <span className="detail-label">Type:</span>
                <Tag
                  value={selectedTask.task_type?.replace('_', ' ')}
                  severity={getTypeSeverity(selectedTask.task_type)}
                />
              </div>
              <div className="detail-item">
                <span className="detail-label">Status:</span>
                <Tag
                  value={selectedTask.status?.replace('_', ' ')}
                  severity={getStatusSeverity(selectedTask.status)}
                />
              </div>
              {selectedTask.description && (
                <div className="detail-item">
                  <span className="detail-label">Description:</span>
                  <p className="detail-value">{selectedTask.description}</p>
                </div>
              )}
            </div>

            <div className="detail-section">
              <h5>Effort & Timeline</h5>
              <div className="detail-row">
                <div className="detail-col">
                  <span className="detail-label">Effort Hours:</span>
                  <span className="detail-value">{selectedTask.effort_hours || '-'} hours</span>
                </div>
                <div className="detail-col">
                  <span className="detail-label">Complexity:</span>
                  <Tag 
                    value={selectedTask.average_complexity || 'N/A'} 
                    severity={selectedTask.average_complexity === 'LOW' ? 'success' : 
                             selectedTask.average_complexity === 'MEDIUM' ? 'warning' : 'danger'}
                  />
                </div>
              </div>
              <div className="detail-row">
                <div className="detail-col">
                  <span className="detail-label">Start Date:</span>
                  <span className="detail-value">
                    {selectedTask.start_date ? new Date(selectedTask.start_date).toLocaleDateString() : '-'}
                  </span>
                </div>
                <div className="detail-col">
                  <span className="detail-label">End Date:</span>
                  <span className="detail-value">
                    {selectedTask.end_date ? new Date(selectedTask.end_date).toLocaleDateString() : '-'}
                  </span>
                </div>
              </div>
            </div>

            <div className="detail-section">
              <h5>Progress</h5>
              <div className="detail-item">
                <span className="detail-label">Completion:</span>
                <div className="progress-bar-large" style={{ width: '100%' }}>
                  <div className="progress-fill" style={{ width: `${selectedTask.completion_percentage || 0}%` }}></div>
                  <span className="progress-text">{selectedTask.completion_percentage || 0}%</span>
                </div>
              </div>
              {selectedTask.covered_topics && selectedTask.covered_topics.length > 0 && (
                <div className="detail-item">
                  <span className="detail-label">Topics Covered:</span>
                  <div className="topics-list">
                    {selectedTask.covered_topics.map((topic, idx) => (
                      <Tag key={idx} value={topic} className="topic-tag" />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {selectedTask.concepts && selectedTask.concepts.length > 0 && (
              <div className="detail-section">
                <h5>Concepts ({selectedTask.concepts.length})</h5>
                <div className="concepts-grid">
                  {selectedTask.concepts.slice(0, 5).map((concept, idx) => (
                    <div key={idx} className="concept-item">
                      <span className="concept-name">{concept.name}</span>
                      <Tag 
                        value={concept.complexity} 
                        severity={concept.complexity === 'LOW' ? 'success' : 
                                 concept.complexity === 'MEDIUM' ? 'warning' : 'danger'}
                        className="concept-complexity"
                      />
                    </div>
                  ))}
                  {selectedTask.concepts.length > 5 && (
                    <div className="concept-item more">+{selectedTask.concepts.length - 5} more</div>
                  )}
                </div>
              </div>
            )}

            {selectedTask.notes && (
              <div className="detail-section">
                <h5>Notes</h5>
                <p className="detail-value">{selectedTask.notes}</p>
              </div>
            )}

            <div className="dialog-footer">
              <Button
                label="Close"
                icon="pi pi-times"
                onClick={() => setTaskDialog(false)}
                className="p-button-secondary"
              />
            </div>
          </div>
        )}
      </Dialog>

      {/* Update Progress Dialog */}
      <Dialog
        visible={progressDialog}
        onHide={() => setProgressDialog(false)}
        header="Update Task Progress"
        modal
        style={{ width: '90vw', maxWidth: '500px' }}
      >
        {selectedTask && (
          <div className="progress-form">
            <div className="form-group">
              <label className="form-label">Status</label>
              <div className="status-selector">
                {['PENDING', 'IN_PROGRESS', 'COMPLETED'].map(status => (
                  <Button
                    key={status}
                    label={status.replace('_', ' ')}
                    className={`p-button-sm ${progressData.status === status ? 'p-button-success' : 'p-button-secondary'}`}
                    onClick={() => setProgressData(prev => ({ ...prev, status }))}
                  />
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Completion Percentage: {progressData.completion_percentage}%</label>
              <InputNumber
                value={progressData.completion_percentage}
                onValueChange={(e) => setProgressData(prev => ({ ...prev, completion_percentage: e.value }))}
                min={0}
                max={100}
                suffix="%"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Start Date</label>
                <Calendar
                  value={progressData.start_date}
                  onChange={(e) => setProgressData(prev => ({ ...prev, start_date: e.value }))}
                  showIcon
                  dateFormat="yy-mm-dd"
                />
              </div>
              <div className="form-group">
                <label className="form-label">End Date</label>
                <Calendar
                  value={progressData.end_date}
                  onChange={(e) => setProgressData(prev => ({ ...prev, end_date: e.value }))}
                  showIcon
                  dateFormat="yy-mm-dd"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Notes</label>
              <InputTextarea
                value={progressData.notes}
                onChange={(e) => setProgressData(prev => ({ ...prev, notes: e.target.value }))}
                rows={4}
                placeholder="Add any notes about the task progress..."
              />
            </div>

            <div className="dialog-footer">
              <Button
                label="Cancel"
                icon="pi pi-times"
                onClick={() => setProgressDialog(false)}
                className="p-button-secondary"
              />
              <Button
                label="Update Progress"
                icon="pi pi-check"
                onClick={handleUpdateProgress}
                loading={updatingProgress}
                className="p-button-success"
              />
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
