import { useState, useEffect, useRef } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { Tag } from 'primereact/tag';
import { Dialog } from 'primereact/dialog';
import './TasksList.css';

export default function TasksList() {
  const toastRef = useRef(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskDialog, setTaskDialog] = useState(false);
  const [globalFilter, setGlobalFilter] = useState('');

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
  );

  const dateTemplate = (rowData, field) => {
    if (!rowData[field]) return '-';
    return new Date(rowData[field]).toLocaleDateString();
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
              style={{ width: '120px' }}
            />
            <Column
              field="status"
              header="Status"
              body={statusTemplate}
              sortable
              style={{ width: '120px' }}
            />
            <Column
              field="created_at"
              header="Created"
              body={(rowData) => dateTemplate(rowData, 'created_at')}
              sortable
              style={{ width: '100px' }}
            />
            <Column
              field="updated_at"
              header="Updated"
              body={(rowData) => dateTemplate(rowData, 'updated_at')}
              sortable
              style={{ width: '100px' }}
            />
            <Column
              header="Action"
              body={actionTemplate}
              style={{ width: '80px', textAlign: 'center' }}
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
            {selectedTask.content && (
              <div className="detail-item">
                <span className="detail-label">Details:</span>
                <div className="detail-content">
                  {typeof selectedTask.content === 'string' ? (
                    <p>{selectedTask.content}</p>
                  ) : (
                    <>
                      {selectedTask.content.learning_objectives && (
                        <div>
                          <strong>Learning Objectives:</strong>
                          <ul>
                            {selectedTask.content.learning_objectives.map((obj, idx) => (
                              <li key={idx}>{obj}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {selectedTask.content.estimated_time_minutes && (
                        <p>
                          <strong>Estimated Time:</strong> ~
                          {selectedTask.content.estimated_time_minutes} minutes
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
            <div className="detail-item">
              <span className="detail-label">Created:</span>
              <span className="detail-value">
                {new Date(selectedTask.created_at).toLocaleString()}
              </span>
            </div>
            {selectedTask.updated_at && (
              <div className="detail-item">
                <span className="detail-label">Last Updated:</span>
                <span className="detail-value">
                  {new Date(selectedTask.updated_at).toLocaleString()}
                </span>
              </div>
            )}
            <div className="dialog-footer">
              <Button
                label="Close"
                icon="pi pi-times"
                onClick={() => setTaskDialog(false)}
                className="p-button-secondary"
              />
              {selectedTask.status !== 'COMPLETED' && (
                <Button
                  label="Mark Complete"
                  icon="pi pi-check"
                  className="p-button-success"
                  onClick={() => {
                    toastRef.current?.show({
                      severity: 'info',
                      summary: 'Feature Coming Soon',
                      detail: 'Task completion feature will be available soon',
                      life: 3000
                    });
                  }}
                />
              )}
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
