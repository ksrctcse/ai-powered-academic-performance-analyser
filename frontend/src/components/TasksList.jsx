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
import { Dropdown } from 'primereact/dropdown';
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
  const [selectedDepartment, setSelectedDepartment] = useState(null);
  const [syllabuses, setSyllabuses] = useState([]);
  const [selectedSyllabus, setSelectedSyllabus] = useState(null);
  const [loadingSyllabuses, setLoadingSyllabuses] = useState(false);
  
  // All department options
  const ALL_DEPARTMENTS = [
    { label: 'Computer Science & Engineering (CSE)', value: 'CSE' },
    { label: 'Information Technology (IT)', value: 'IT' },
    { label: 'Electronics & Communication (ECE)', value: 'ECE' },
    { label: 'Electrical & Electronics (EEE)', value: 'EEE' },
    { label: 'Mechanical (MECH)', value: 'MECH' },
    { label: 'Civil (CIVIL)', value: 'CIVIL' }
  ];

  // Get unique departments from current staff's syllabuses
  const departmentsWithSyllabuses = [...new Set(syllabuses.map(s => s.department).filter(Boolean))];
  
  // Only show departments that have uploaded syllabuses, plus "All Departments" option
  const departmentOptions = [
    { label: 'All Departments', value: null },
    ...ALL_DEPARTMENTS.filter(dept => departmentsWithSyllabuses.includes(dept.value))
  ];
  
  const [progressData, setProgressData] = useState({
    status: 'IN_PROGRESS',
    completion_percentage: 0,
    start_date: null,
    end_date: null,
    covered_topics: [],
    notes: '',
    learning_task_progress: []  // Array of {task_title, completion_percentage, status, notes}
  });
  const [deleteTaskData, setDeleteTaskData] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Fetch syllabuses on component mount
  useEffect(() => {
    fetchSyllabuses();
  }, []);

  const fetchSyllabuses = async () => {
    setLoadingSyllabuses(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        'http://localhost:8000/syllabus/list',
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch syllabuses');
      }

      const result = await response.json();
      if (result.success && result.data) {
        setSyllabuses(result.data);
      }
    } catch (error) {
      console.error('Error fetching syllabuses:', error);
    } finally {
      setLoadingSyllabuses(false);
    }
  };

  // Get filtered syllabuses based on selected department
  const filteredSyllabuses = selectedDepartment
    ? syllabuses.filter(s => s.department === selectedDepartment)
    : syllabuses;

  const syllabusOptions = filteredSyllabuses.map(s => ({
    label: `${s.course_name} | ${s.department || 'N/A'} | ${s.file_type}`,
    value: s
  }));

  // Fetch tasks on component mount and when filters change
  useEffect(() => {
    fetchTasks();
  }, [selectedDepartment, selectedSyllabus]);

  // Listen for syllabus deletion events to refresh the list
  useEffect(() => {
    const handleStorageChange = () => {
      const deletionEvent = localStorage.getItem('syllabusDeleted');
      if (deletionEvent) {
        try {
          const { syllabusId: deletedId } = JSON.parse(deletionEvent);
          
          // Clear selected syllabus if it was the one that was deleted
          if (selectedSyllabus?.id === deletedId) {
            setSelectedSyllabus(null);
            toastRef.current?.show({
              severity: 'warn',
              summary: 'Syllabus Deleted',
              detail: 'The selected syllabus has been deleted. Filters have been reset.',
              life: 3000
            });
          }
          
          // Remove from syllabuses list
          setSyllabuses(prev => prev.filter(s => s.id !== deletedId));
        } catch (e) {
          console.error('Error processing deletion event:', e);
        }
      }
    };

    // Listen for storage changes
    window.addEventListener('storage', handleStorageChange);
    handleStorageChange();
    
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [selectedSyllabus?.id]);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const userId = JSON.parse(localStorage.getItem('user'))?.id;

      let url = `http://localhost:8000/tasks?staff_id=${userId}`;
      if (selectedDepartment) {
        url += `&department=${selectedDepartment}`;
      }
      if (selectedSyllabus?.id) {
        url += `&syllabus_id=${selectedSyllabus.id}`;
      }

      const response = await fetch(
        url,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      // If syllabus not found (404), clear it from selection
      if (response.status === 404) {
        setSyllabuses(prev => prev.filter(s => s.id !== selectedSyllabus?.id));
        setSelectedSyllabus(null);
        toastRef.current?.show({
          severity: 'warn',
          summary: 'Syllabus Not Found',
          detail: 'The selected syllabus no longer exists. Please select another.',
          life: 3000
        });
        setTasks([]);
        return;
      }

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

  const getProgressButtonClass = (status) => {
    switch(status) {
      case 'PENDING':
        return 'p-button-warning';
      case 'IN_PROGRESS':
        return 'p-button-info';
      case 'COMPLETED':
        return 'p-button-success';
      default:
        return 'p-button-info';
    }
  };

  const calculateAverageProgressAndStatus = (learningTasks) => {
    if (!learningTasks || learningTasks.length === 0) {
      return { avgPercentage: 0, overallStatus: 'PENDING' };
    }

    const totalPercentage = learningTasks.reduce((sum, task) => sum + (task.completion_percentage || 0), 0);
    const avgPercentage = Math.round(totalPercentage / learningTasks.length);
    
    // Check if any task has started (> 0%)
    const anyTaskStarted = learningTasks.some(task => (task.completion_percentage || 0) > 0);
    
    // Check if all tasks are 100% completed
    const allTasksCompleted = learningTasks.every(task => (task.completion_percentage || 0) === 100);
    
    // Determine overall status based on requirements
    let overallStatus = 'PENDING';
    if (allTasksCompleted && avgPercentage === 100) {
      // All tasks are 100% - mark as COMPLETED
      overallStatus = 'COMPLETED';
    } else if (anyTaskStarted) {
      // If any task > 0% - mark as IN_PROGRESS
      overallStatus = 'IN_PROGRESS';
    }
    // else: all tasks are 0% - stay as PENDING
    
    return { avgPercentage, overallStatus };
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
        className="p-button-sm p-button-secondary"
        onClick={() => {
          setSelectedTask(rowData);
          setTaskDialog(true);
        }}
        tooltip="View Details"
        tooltipPosition="bottom"
      />
      <Button
        icon="pi pi-chart-line"
        rounded
        className={`p-button-sm ${getProgressButtonClass(rowData.status)}`}
        onClick={() => {
          setSelectedTask(rowData);
          // Initialize learning task progress from content.generated_tasks if available
          let learningTaskProgress = [];
          if (rowData.learning_task_progress && rowData.learning_task_progress.length > 0) {
            learningTaskProgress = rowData.learning_task_progress;
          } else if (rowData.content?.generated_tasks) {
            learningTaskProgress = rowData.content.generated_tasks.map(task => ({
              task_title: task.title,
              task_type: task.type,
              difficulty: task.difficulty,
              estimated_time_minutes: task.estimated_time_minutes,
              completion_percentage: 0,
              status: 'PENDING',
              notes: ''
            }));
          }
          
          setProgressData({
            status: rowData.status || 'IN_PROGRESS',
            completion_percentage: rowData.completion_percentage || 0,
            start_date: rowData.start_date ? new Date(rowData.start_date) : null,
            end_date: rowData.end_date ? new Date(rowData.end_date) : null,
            covered_topics: rowData.covered_topics || [],
            notes: rowData.notes || '',
            learning_task_progress: learningTaskProgress
          });
          setProgressDialog(true);
        }}
        tooltip="Update Progress"
        tooltipPosition="bottom"
      />
      {rowData.status !== 'COMPLETED' && (
        <Button
          icon="pi pi-trash"
          rounded
          className="p-button-sm p-button-danger"
          onClick={() => handleDeleteTask(rowData)}
          tooltip="Delete Task"
          tooltipPosition="bottom"
        />
      )}
    </div>
  );

  const handleDeleteTask = (rowData) => {
    setDeleteTaskData(rowData);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteTask = async () => {
    if (!deleteTaskData) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/tasks/${deleteTaskData.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to delete task: ${response.statusText}`);
      }

      toastRef.current?.show({
        severity: 'success',
        summary: 'Success',
        detail: 'Task deleted successfully',
        life: 3000
      });
      
      setShowDeleteConfirm(false);
      setDeleteTaskData(null);
      fetchTasks(); // Refresh tasks list
    } catch (error) {
      console.error('Error deleting task:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to delete task',
        life: 3000
      });
    }
  };

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
        notes: progressData.notes,
        learning_task_progress: progressData.learning_task_progress // Include individual learning task progress
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
    <>
      <div className="tasks-list-container">
      <Toast ref={toastRef} position="top-right" />

      <Card className="tasks-card">
        <div className="tasks-header">
          <h3>📋 All Assigned Tasks</h3>
          <div className="filters-section" style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            {/* Department Filter */}
            <div className="department-filter-section">
              <label style={{ marginRight: '0.5rem', fontWeight: '500' }}>📋 Department:</label>
              <Dropdown
                value={selectedDepartment}
                onChange={(e) => {
                  setSelectedDepartment(e.value);
                  setSelectedSyllabus(null); // Reset syllabus when department changes
                }}
                options={departmentOptions}
                placeholder="Select a department"
                style={{ width: '250px' }}
                emptyMessage={departmentOptions.length <= 1 ? "No departments with syllabuses" : ""}
              />
            </div>

            {/* Syllabus Filter */}
            <div className="syllabus-filter-section">
              <label style={{ marginRight: '0.5rem', fontWeight: '500' }}>📚 Syllabus:</label>
              <Dropdown
                value={selectedSyllabus}
                onChange={(e) => setSelectedSyllabus(e.value)}
                options={syllabusOptions}
                optionLabel="label"
                optionValue="value"
                placeholder={loadingSyllabuses ? "Loading..." : "Select a syllabus"}
                disabled={loadingSyllabuses || filteredSyllabuses.length === 0}
                style={{ width: '250px' }}
                showClear
                emptyMessage={filteredSyllabuses.length === 0 ? (selectedDepartment ? "No syllabuses for this department" : "Select department first") : ""}
              />
            </div>
          </div>
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
            scrollable
            responsiveLayout="scroll"
          >
            <Column field="title" header="Title" sortable filter style={{ minWidth: '200px' }} />
            <Column 
              field="department" 
              header="Department" 
              sortable 
              style={{ width: '90px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
            />
            <Column
              field="task_type"
              header="Type"
              body={typeTemplate}
              sortable
              style={{ width: '80px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
            />
            <Column
              field="status"
              header="Status"
              body={statusTemplate}
              sortable
              style={{ width: '80px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
            />
            <Column
              field="completion_percentage"
              header="Progress"
              body={completionTemplate}
              style={{ width: '100px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
            />
            <Column
              field="effort_hours"
              header="Effort"
              body={effortTemplate}
              sortable
              style={{ width: '70px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
            />
            <Column
              field="average_complexity"
              header="Complexity"
              body={complexityTemplate}
              sortable
              style={{ width: '90px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
            />
            <Column
              field="start_date"
              header="Start Date"
              body={(rowData) => dateTemplate(rowData, 'start_date')}
              sortable
              style={{ width: '105px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
            />
            <Column
              field="end_date"
              header="End Date"
              body={(rowData) => dateTemplate(rowData, 'end_date')}
              sortable
              style={{ width: '105px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
            />
            <Column
              header="Action"
              body={actionTemplate}
              style={{ width: '70px' }}
              headerStyle={{ textAlign: 'center' }}
              bodyStyle={{ textAlign: 'center' }}
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
            <div className="detail-section">
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

            {selectedTask.content && selectedTask.content.generated_tasks && selectedTask.content.generated_tasks.length > 0 && (
              <div className="detail-section">
                <h5>📚 Generated Learning Tasks ({selectedTask.content.generated_tasks.length})</h5>
                <div className="generated-tasks-list">
                  {selectedTask.content.generated_tasks.map((task, idx) => (
                    <div key={idx} className="generated-task-item">
                      <div className="task-header">
                        <span className="task-number">{idx + 1}</span>
                        <span className="task-title">{task.title}</span>
                        <Tag 
                          value={task.type?.replace(/_/g, ' ').toUpperCase()} 
                          severity={task.type === 'quiz' ? 'info' : task.type === 'practical_lab' ? 'success' : 'warning'}
                          style={{ fontSize: '11px' }}
                        />
                        <Tag 
                          value={task.difficulty?.replace(/_/g, ' ').toUpperCase()} 
                          severity={task.difficulty?.includes('easy') ? 'success' : task.difficulty?.includes('medium') ? 'warning' : 'danger'}
                          style={{ fontSize: '11px' }}
                        />
                      </div>
                      <div className="task-content-preview">
                        <p><strong>Description:</strong> {task.description}</p>
                        <div className="task-details-row">
                          <span><strong>Type:</strong> {task.type?.replace(/_/g, ' ')}</span>
                          <span><strong>Difficulty:</strong> {task.difficulty?.replace(/_/g, ' ')}</span>
                          <span><strong>Time:</strong> {task.estimated_time_minutes} mins</span>
                        </div>
                        {task.learning_objectives && task.learning_objectives.length > 0 && (
                          <div className="learning-objectives">
                            <strong>Learning Objectives:</strong>
                            <ul>
                              {task.learning_objectives.slice(0, 3).map((obj, i) => (
                                <li key={i}>{obj}</li>
                              ))}
                              {task.learning_objectives.length > 3 && (
                                <li>+{task.learning_objectives.length - 3} more objectives...</li>
                              )}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
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
              <label className="form-label">Status (Auto-Calculated)</label>
              <div className="status-display">
                <Tag 
                  value={progressData.status?.replace('_', ' ') || 'PENDING'} 
                  severity={getStatusSeverity(progressData.status)}
                  style={{ fontSize: '12px', fontWeight: '600', minWidth: '100px' }}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                {progressData.learning_task_progress && progressData.learning_task_progress.length > 0 
                  ? `Overall Completion Percentage (auto-calculated): ${progressData.completion_percentage}%`
                  : `Completion Percentage: ${progressData.completion_percentage}%`
                }
              </label>
              <InputNumber
                value={progressData.completion_percentage}
                onValueChange={(e) => setProgressData(prev => ({ ...prev, completion_percentage: e.value }))}
                min={0}
                max={100}
                suffix="%"
                disabled={progressData.learning_task_progress && progressData.learning_task_progress.length > 0}
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

            {progressData.learning_task_progress && progressData.learning_task_progress.length > 0 && (
              <div className="form-group">
                <label className="form-label">📚 Individual Learning Task Progress</label>
                <div className="learning-tasks-progress">
                  {progressData.learning_task_progress.map((learningTask, idx) => (
                    <div key={idx} className="learning-task-progress-item">
                      <div className="task-progress-header">
                        <span className="task-progress-title">{learningTask.task_title}</span>
                        <span className="task-progress-completion">{learningTask.completion_percentage}%</span>
                      </div>
                      <div className="task-progress-controls">
                        <InputNumber
                          value={learningTask.completion_percentage}
                          onValueChange={(e) => {
                            const updated = [...progressData.learning_task_progress];
                            updated[idx].completion_percentage = e.value || 0;
                            updated[idx].status = e.value === 100 ? 'COMPLETED' : (e.value > 0 ? 'IN_PROGRESS' : 'PENDING');
                            
                            // Calculate average progress and status from all learning tasks
                            const { avgPercentage, overallStatus } = calculateAverageProgressAndStatus(updated);
                            
                            setProgressData(prev => ({ 
                              ...prev, 
                              learning_task_progress: updated,
                              completion_percentage: avgPercentage,
                              status: overallStatus
                            }));
                          }}
                          min={0}
                          max={100}
                          suffix="%"
                          className="task-progress-input"
                          placeholder="0%"
                        />
                        <Tag
                          value={learningTask.status || 'PENDING'}
                          severity={
                            learningTask.status === 'COMPLETED' ? 'success' : 
                            learningTask.status === 'IN_PROGRESS' ? 'info' : 'warning'
                          }
                          style={{ fontSize: '11px' }}
                        />
                      </div>
                      <div className="task-progress-bar">
                        <div className="progress-fill" style={{ width: `${learningTask.completion_percentage}%` }}></div>
                      </div>
                      <small className="task-meta-info">
                        {learningTask.task_type && `Type: ${learningTask.task_type.replace(/_/g, ' ')} • `}
                        {learningTask.difficulty && `Difficulty: ${learningTask.difficulty.replace(/_/g, ' ').toUpperCase()} • `}
                        {learningTask.estimated_time_minutes && `${learningTask.estimated_time_minutes} mins`}
                      </small>
                    </div>
                  ))}
                </div>
              </div>
            )}

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
              onClick={confirmDeleteTask} 
              className="p-button-danger"
            />
          </div>
        }
      >
        <p>
          Are you sure you want to delete the task <strong>"{deleteTaskData?.title}"</strong>? This action cannot be undone.
        </p>
      </Dialog>
    </div>
    </>
  );
}
