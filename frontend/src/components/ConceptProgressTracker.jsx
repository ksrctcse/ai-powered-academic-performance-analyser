import { useRef, useState, useEffect } from 'react';
import { Dropdown } from 'primereact/dropdown';
import { MultiSelect } from 'primereact/multiselect';
import { Calendar } from 'primereact/calendar';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { Tabs } from 'primereact/tabs';
import { TabPanel } from 'primereact/tabpanel';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Badge } from 'primereact/badge';
import './ConceptProgressTracker.css';

export default function ConceptProgressTracker({ syllabusId = null, onProgressUpdate = null }) {
  const toastRef = useRef(null);
  
  // State for hierarchy and selection
  const [loading, setLoading] = useState(false);
  const [loadingSyllabuses, setLoadingSyllabuses] = useState(false);
  const [syllabuses, setSyllabuses] = useState([]);
  const [selectedSyllabus, setSelectedSyllabus] = useState(null);
  const [hierarchyData, setHierarchyData] = useState(null);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [selectedConcepts, setSelectedConcepts] = useState([]);
  const [topicOptions, setTopicOptions] = useState([]);
  const [conceptOptions, setConceptOptions] = useState([]);

  // State for dates and progress
  const [startDates, setStartDates] = useState({}); // concept_id -> date
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [progressSubmitting, setProgressSubmitting] = useState(false);
  const [taskDialog, setTaskDialog] = useState(false);
  const [generatedTasks, setGeneratedTasks] = useState([]);
  const [completedConcepts, setCompletedConcepts] = useState([]);

  // Fetch available syllabuses only when explicitly needed (not on mount)
  useEffect(() => {
    // If syllabus ID is provided externally, use it
    if (syllabusId) {
      setSelectedSyllabus({ id: syllabusId });
    }
    // Otherwise, fetch syllabuses on mount so dropdown is enabled
    else if (syllabuses.length === 0 && !loadingSyllabuses) {
      fetchSyllabuses();
    }
  }, [syllabusId, syllabuses.length, loadingSyllabuses]);

  // Fetch list of syllabuses
  const fetchSyllabuses = async () => {
    setLoadingSyllabuses(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:8000/syllabus/list`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) throw new Error('Failed to fetch syllabuses');

      const result = await response.json();
      if (result.success && result.data) {
        setSyllabuses(result.data);
        if (result.data.length === 0) {
          toastRef.current?.show({
            severity: 'warn',
            summary: 'No Syllabuses Found',
            detail: 'Please upload a syllabus first',
            life: 3000
          });
        }
      }
    } catch (error) {
      console.error('Error fetching syllabuses:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load syllabuses',
        life: 3000
      });
    } finally {
      setLoadingSyllabuses(false);
    }
  };

  // Fetch unit->topic->concepts data from backend
  const fetchHierarchyData = async () => {
    if (!selectedSyllabus?.id) {
      toastRef.current?.show({
        severity: 'warn',
        summary: 'No Syllabus Selected',
        detail: 'Please select a syllabus first',
        life: 3000
      });
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `http://localhost:8000/syllabus/${selectedSyllabus.id}/units-topics-concepts`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) throw new Error('Failed to fetch hierarchy data');

      const result = await response.json();
      if (result.success && result.data.units) {
        setHierarchyData(result.data);
        toastRef.current?.show({
          severity: 'success',
          summary: 'Hierarchy Loaded',
          detail: `Loaded ${result.data.total_units} units with ${result.data.total_concepts} concepts`,
          life: 2000
        });
      }
    } catch (error) {
      console.error('Error fetching hierarchy:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to load hierarchy data',
        life: 3000
      });
    } finally {
      setLoading(false);
    }
  };

  // Reset dependent selections when unit changes
  useEffect(() => {
    setSelectedTopic(null);
    setSelectedConcepts([]);
    setConceptOptions([]);

    if (selectedUnit && hierarchyData) {
      const unit = hierarchyData.units.find(u => u.unit_id === selectedUnit.unit_id);
      if (unit) {
        const topics = unit.topics.map(t => ({
          label: t.topic_name,
          value: t.topic_id,
          topic_obj: t
        }));
        setTopicOptions(topics);
      }
    }
  }, [selectedUnit, hierarchyData]);

  // Update concepts when topic changes
  useEffect(() => {
    setSelectedConcepts([]);

    if (selectedTopic && topicOptions) {
      const topic = topicOptions.find(t => t.value === selectedTopic);
      if (topic && topic.topic_obj) {
        const concepts = topic.topic_obj.concepts.map(c => ({
          value: c.id || `${selectedUnit.unit_id}_${selectedTopic}_${c.concept_name}`,
          label: c.concept_name,
          name: c.concept_name,
          complexity: c.complexity_level,
          concept_obj: c
        }));
        setConceptOptions(concepts);
      }
    }
  }, [selectedTopic, topicOptions]);

  // Handle syllabus selection
  const handleSyllabusSelect = (e) => {
    setSelectedSyllabus(e.value);
    setHierarchyData(null);
    setSelectedUnit(null);
    setSelectedTopic(null);
    setSelectedConcepts([]);
  };

  // Handle unit selection
  const handleUnitChange = (e) => {
    setSelectedUnit(e.value);
  };

  // Handle topic selection
  const handleTopicChange = (e) => {
    setSelectedTopic(e.value);
    if (e.value) {
      const topic = topicOptions.find(t => t.value === e.value);
      toastRef.current?.show({
        severity: 'info',
        summary: 'Topic Selected',
        detail: `${topic?.label} selected`,
        life: 2000
      });
    }
  };

  // Handle concepts change
  const handleConceptsChange = (e) => {
    setSelectedConcepts(e.value);
    if (e.value?.length > 0) {
      toastRef.current?.show({
        severity: 'success',
        summary: 'Concepts Selected',
        detail: `${e.value.length} concept(s) selected for tracking`,
        life: 2000
      });
    }
  };

  // Handle start date selection
  const handleStartDateChange = (conceptId, date) => {
    setStartDates(prev => ({
      ...prev,
      [conceptId]: date
    }));
  };

  // Submit concept progress
  const handleStartProgress = async () => {
    if (selectedConcepts.length === 0) {
      toastRef.current?.show({
        severity: 'warn',
        summary: 'No Concepts Selected',
        detail: 'Please select at least one concept',
        life: 2000
      });
      return;
    }

    setProgressSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const userId = JSON.parse(localStorage.getItem('user'))?.id;

      // Submit progress for each selected concept
      const results = [];
      for (const conceptId of selectedConcepts) {
        const startDate = startDates[conceptId] || new Date();
        const concept = conceptOptions.find(c => c.value === conceptId);

        const response = await fetch(
          `http://localhost:8000/progress/concept/start`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              unit_topic_concept_id: conceptId,
              staff_id: userId,
              start_date: startDate.toISOString(),
              status: 'In Progress',
              completion_percentage: 0
            })
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to start progress for ${concept?.name}`);
        }

        const result = await response.json();
        results.push(result.data);
      }

      toastRef.current?.show({
        severity: 'success',
        summary: 'Progress Started',
        detail: `Started tracking ${selectedConcepts.length} concept(s)`,
        life: 3000
      });

      if (onProgressUpdate) {
        onProgressUpdate(results);
      }

      // Reset form
      setSelectedConcepts([]);
      setStartDates({});
      setShowProgressDialog(false);

    } catch (error) {
      console.error('Error starting progress:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.message || 'Failed to start progress tracking',
        life: 3000
      });
    } finally {
      setProgressSubmitting(false);
    }
  };

  // Assign progress as tasks
  const handleAssignAsTasks = async () => {
    if (selectedConcepts.length === 0) {
      toastRef.current?.show({
        severity: 'warn',
        summary: 'No Concepts Selected',
        detail: 'Please select at least one concept',
        life: 2000
      });
      return;
    }

    setProgressSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const userId = JSON.parse(localStorage.getItem('user'))?.id;

      // Create task for each selected concept
      let tasksCreated = 0;
      for (const conceptId of selectedConcepts) {
        const concept = conceptOptions.find(c => c.value === conceptId);
        const topic = topicOptions.find(t => t.value === selectedTopic);

        const response = await fetch(
          `http://localhost:8000/tasks/assign`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              unit_topic_concept_id: conceptId,
              staff_id: userId,
              title: `Learn: ${concept?.name}`,
              description: `Master the concept of ${concept?.name} under ${topic?.label || 'topic'}`,
              task_type: 'READING',
              status: 'PENDING',
              content: {
                concept_name: concept?.name,
                topic_name: topic?.label,
                complexity: concept?.complexity,
                learning_objectives: [
                  `Understand ${concept?.name}`,
                  `Apply knowledge of ${concept?.name}`,
                  `Analyze ${concept?.name} in depth`
                ],
                estimated_time_minutes: concept?.complexity === 'HIGH' ? 120 : concept?.complexity === 'MEDIUM' ? 60 : 30
              }
            })
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to assign task for ${concept?.name}`);
        }

        tasksCreated++;
      }

      toastRef.current?.show({
        severity: 'success',
        summary: 'Tasks Assigned Successfully',
        detail: `Created ${tasksCreated} task(s) for selected concepts`,
        life: 3000
      });

      // Reset form
      setSelectedConcepts([]);
      setStartDates({});

    } catch (error) {
      console.error('Error assigning tasks:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.message || 'Failed to assign tasks',
        life: 3000
      });
    } finally {
      setProgressSubmitting(false);
    }
  };

  // Complete concept progress and generate tasks
  const handleCompleteProgress = async (conceptId) => {
    setProgressSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const userId = JSON.parse(localStorage.getItem('user'))?.id;
      const endDate = new Date();

      const response = await fetch(
        `http://localhost:8000/progress/concept/complete`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            unit_topic_concept_id: conceptId,
            staff_id: userId,
            end_date: endDate.toISOString(),
            completion_percentage: 100,
            generate_tasks: true
          })
        }
      );

      if (!response.ok) {
        throw new Error('Failed to complete progress');
      }

      const result = await response.json();
      const concept = conceptOptions.find(c => c.value === conceptId);

      toastRef.current?.show({
        severity: 'success',
        summary: 'Concept Completed',
        detail: `${concept?.name} marked as complete. Generated ${result.data.tasks_generated} tasks.`,
        life: 3000
      });

      // Show generated tasks
      setGeneratedTasks(result.data.tasks || []);
      setCompletedConcepts(prev => [...prev, conceptId]);
      setTaskDialog(true);

    } catch (error) {
      console.error('Error completing progress:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.message || 'Failed to complete progress',
        life: 3000
      });
    } finally {
      setProgressSubmitting(false);
    }
  };

  // Setup dropdown options
  const unitOptions = hierarchyData?.units?.map(u => ({
    label: u.unit_name,
    value: {
      unit_id: u.unit_id,
      unit_name: u.unit_name
    }
  })) || [];

  const syllabusOptions = syllabuses.map(s => ({
    label: `${s.course_name} | ${s.department || 'N/A'} | ${s.file_type}`,
    value: s
  }));

  const getComplexityColor = (level) => {
    switch (level) {
      case 'LOW':
        return '#22c55e';
      case 'MEDIUM':
        return '#eab308';
      case 'HIGH':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className="unit-concept-selector">
      <Toast ref={toastRef} position="top-right" />

      <Card className="selection-card">
        <div className="selection-header">
          <h3>📚 Concept Progress Tracker</h3>
          {selectedSyllabus && hierarchyData && (
            <p className="text-sm text-gray-600">
              {hierarchyData.course_name} | Units: {hierarchyData.total_units} | Concepts: {hierarchyData.total_concepts}
            </p>
          )}
          {!selectedSyllabus && (
            <p className="text-sm text-gray-600">
              Select a syllabus to track your learning progress
            </p>
          )}
        </div>

        <Tabs>
          {/* Tab 1: Syllabus & Concept Selection */}
          <TabPanel header="📖 Select Concepts" leftIcon="pi pi-fw pi-book">
            {!selectedSyllabus || !hierarchyData ? (
              <div className="syllabus-selection-section">
                {/* Syllabus Selection */}
                <div className="form-group">
                  <label htmlFor="syllabus-select">Step 1: Select a Syllabus *</label>
                  <div className="input-group">
                    <Dropdown
                      id="syllabus-select"
                      placeholder={loadingSyllabuses ? "Loading syllabuses..." : "Choose a syllabus..."}
                      options={syllabusOptions}
                      value={selectedSyllabus}
                      onChange={handleSyllabusSelect}
                      onShow={() => {
                        // Refresh syllabuses when dropdown opens (in case new ones were added)
                        if (!loadingSyllabuses) {
                          fetchSyllabuses();
                        }
                      }}
                      className="w-full"
                      optionLabel="label"
                      optionValue="value"
                      loading={loadingSyllabuses}
                      disabled={loadingSyllabuses}
                      emptyMessage={syllabuses.length === 0 ? "No syllabuses found. Please upload one first." : ""}
                      filter
                    />
                    {loadingSyllabuses && (
                      <small className="text-blue-600">Loading syllabuses...</small>
                    )}
                  </div>

                  {syllabuses.length === 0 && !loadingSyllabuses && (
                    <div className="empty-state">
                      <p className="text-red-600">
                        No syllabuses found. Please upload a syllabus first.
                      </p>
                    </div>
                  )}

                  {selectedSyllabus && !hierarchyData && (
                    <div className="load-section">
                      <p className="section-subtitle">Step 2: Load the Hierarchy</p>
                      <Button
                        label="Load Hierarchy from Syllabus"
                        icon="pi pi-download"
                        onClick={fetchHierarchyData}
                        loading={loading}
                        className="p-button-primary"
                        size="large"
                      />
                      {loading && (
                        <div className="loading-container">
                          <ProgressSpinner style={{ width: '50px', height: '50px' }} />
                          <p>Fetching hierarchy data...</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="selection-form">
                {/* Unit Selection */}
                <div className="form-group">
                  <label htmlFor="unit-select">Step 3: Select a Unit *</label>
                  <Dropdown
                    id="unit-select"
                    placeholder="Select a unit"
                    options={unitOptions}
                    value={selectedUnit}
                    onChange={handleUnitChange}
                    className="w-full"
                    optionLabel="label"
                  />
                  {selectedUnit && (
                    <small className="text-blue-600">
                      Selected: {selectedUnit.unit_name}
                    </small>
                  )}
                </div>

                {selectedUnit && (
                  <div className="form-group">
                    <label htmlFor="topic-select">Step 4: Select a Topic *</label>
                    <Dropdown
                      id="topic-select"
                      placeholder="Select a topic"
                      options={topicOptions}
                      value={selectedTopic}
                      onChange={handleTopicChange}
                      className="w-full"
                      optionLabel="label"
                      disabled={topicOptions.length === 0}
                    />
                    {selectedTopic && (
                      <small className="text-blue-600">
                        Selected: {topicOptions.find(t => t.value === selectedTopic)?.label}
                      </small>
                    )}
                  </div>
                )}

                {selectedTopic && (
                  <div className="form-group">
                    <label htmlFor="concepts-select">Step 5: Select Concepts *</label>
                    <MultiSelect
                      id="concepts-select"
                      placeholder="Select concepts to track"
                      options={conceptOptions}
                      value={selectedConcepts}
                      onChange={handleConceptsChange}
                      className="w-full"
                      optionLabel="label"
                      disabled={conceptOptions.length === 0}
                      maxSelectedLabels={3}
                      display="chip"
                    />
                    <div className="concepts-complexity-info">
                      {selectedConcepts.length > 0 && (
                        <div className="complexity-badges">
                          {selectedConcepts.map(id => {
                            const concept = conceptOptions.find(c => c.value === id);
                            return (
                              <div
                                key={id}
                                className="complexity-badge"
                                style={{
                                  backgroundColor: getComplexityColor(concept?.complexity),
                                  color: 'white'
                                }}
                              >
                                {concept?.name} - {concept?.complexity}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {selectedConcepts.length > 0 && (
                  <div className="form-group">
                    <label>Step 6: Set Start Dates (Optional)</label>
                    <div className="date-picker-group">
                      {selectedConcepts.map((conceptId, index) => {
                        const concept = conceptOptions.find(c => c.value === conceptId);
                        return (
                          <div key={conceptId} className="date-picker-item">
                            <label>{concept?.name}</label>
                            <Calendar
                              value={startDates[conceptId] || new Date()}
                              onChange={(e) => handleStartDateChange(conceptId, e.value)}
                              showTime
                              dateFormat="yy-mm-dd"
                              placeholder="Select start date"
                            />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {selectedConcepts.length > 0 && (
                  <div className="selection-summary-table-section">
                    <div className="summary-info-header">
                      <div className="info-item">
                        <span className="info-label">Syllabus:</span>
                        <span className="info-value">{selectedSyllabus?.course_name}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Unit:</span>
                        <span className="info-value">{selectedUnit?.unit_name}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Topic:</span>
                        <span className="info-value">
                          {topicOptions.find(t => t.value === selectedTopic)?.label}
                        </span>
                      </div>
                    </div>

                    <Card className="summary-table-card">
                      <div className="table-header-section">
                        <h4 className="table-title">
                          <i className="pi pi-list"></i>
                          Selected Concepts ({selectedConcepts.length})
                        </h4>
                      </div>

                      <DataTable 
                        value={selectedConcepts.map((id, index) => {
                          const concept = conceptOptions.find(c => c.value === id);
                          return {
                            id,
                            number: index + 1,
                            name: concept?.name,
                            complexity: concept?.complexity,
                            status: 'Not Started',
                            progress: 0
                          };
                        })}
                        className="summary-concepts-table"
                        stripedRows
                        responsiveLayout="scroll"
                      >
                        <Column 
                          field="number" 
                          header="No." 
                          style={{ width: '60px' }}
                          body={(rowData) => (
                            <div className="table-number">{rowData.number}</div>
                          )}
                        />
                        <Column 
                          field="name" 
                          header="Concept Name" 
                          style={{ width: '40%' }}
                          body={(rowData) => (
                            <div className="concept-name-cell">{rowData.name}</div>
                          )}
                        />
                        <Column 
                          field="complexity" 
                          header="Complexity" 
                          style={{ width: '120px' }}
                          body={(rowData) => (
                            <Badge 
                              value={rowData.complexity}
                              style={{
                                backgroundColor: getComplexityColor(rowData.complexity),
                                color: 'white'
                              }}
                              className="complexity-badge-table"
                            />
                          )}
                        />
                        <Column 
                          field="status" 
                          header="Status" 
                          style={{ width: '120px' }}
                          body={(rowData) => (
                            <Badge 
                              value={rowData.status}
                              severity="warning"
                              className="status-badge"
                            />
                          )}
                        />
                        <Column 
                          field="progress" 
                          header="Progress" 
                          style={{ width: '100px' }}
                          body={(rowData) => (
                            <div className="progress-cell">
                              <div className="progress-bar">
                                <div 
                                  className="progress-fill"
                                  style={{ width: `${rowData.progress}%` }}
                                ></div>
                              </div>
                              <span className="progress-text">{rowData.progress}%</span>
                            </div>
                          )}
                        />
                      </DataTable>

                      <div className="summary-footer-info">
                        <i className="pi pi-info-circle"></i>
                        <span>
                          You have selected <strong>{selectedConcepts.length}</strong> concept(s) for learning. 
                          Click the button below to begin tracking your progress.
                        </span>
                      </div>
                    </Card>
                  </div>
                )}

                {selectedConcepts.length > 0 && (
                  <div className="action-buttons-group">
                    <Button
                      label="Start Tracking Progress"
                      icon="pi pi-play"
                      onClick={handleStartProgress}
                      loading={progressSubmitting}
                      className="p-button-success p-button-lg"
                      style={{ flex: 1 }}
                    />
                    <Button
                      label="Assign as Tasks"
                      icon="pi pi-check-square"
                      onClick={handleAssignAsTasks}
                      loading={progressSubmitting}
                      className="p-button-info p-button-lg"
                      style={{ flex: 1 }}
                    />
                  </div>
                )}

                {/* Change Syllabus Button */}
                <div className="change-syllabus-section">
                  <Button
                    label="Change Syllabus"
                    icon="pi pi-arrow-left"
                    onClick={() => {
                      setSelectedSyllabus(null);
                      setHierarchyData(null);
                      setSelectedUnit(null);
                      setSelectedTopic(null);
                      setSelectedConcepts([]);
                    }}
                    className="p-button-secondary p-button-sm"
                  />
                </div>
              </div>
            )}
          </TabPanel>

          {/* Tab 2: Progress Overview */}
          <TabPanel header="📊 My Progress" leftIcon="pi pi-fw pi-chart-bar">
            <div className="progress-overview">
              <p>Your concept progress will be displayed here.</p>
              <p>Completed concepts: {completedConcepts.length}</p>
            </div>
          </TabPanel>
        </Tabs>
      </Card>

      {/* Task Dialog */}
      <Dialog
        visible={taskDialog}
        onHide={() => setTaskDialog(false)}
        header="🎯 Generated Learning Tasks"
        modal
        style={{ width: '90vw', maxWidth: '900px' }}
      >
        {generatedTasks.length > 0 ? (
          <div className="tasks-container">
            {generatedTasks.map((task, index) => (
              <Card key={index} className="task-card">
                <h4>{task.title}</h4>
                <p>{task.description}</p>
                <div className="task-meta">
                  <span className="task-badge">{task.type}</span>
                  <span className="task-badge">{task.difficulty}</span>
                  <span className="task-badge">~{task.estimated_time_minutes} min</span>
                </div>
                {task.learning_objectives && (
                  <div className="task-objectives">
                    <strong>Learning Objectives:</strong>
                    <ul>
                      {task.learning_objectives.map((obj, idx) => (
                        <li key={idx}>{obj}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>
            ))}
          </div>
        ) : (
          <p>No tasks generated yet.</p>
        )}
      </Dialog>
    </div>
  );
}
