import { useRef, useState, useEffect } from 'react';
import { Dropdown } from 'primereact/dropdown';
import { MultiSelect } from 'primereact/multiselect';
import { Toast } from 'primereact/toast';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Card } from 'primereact/card';
import { Button } from 'primereact/button';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Dialog } from 'primereact/dialog';
import './UnitConceptSelector.css';

export default function UnitConceptSelector({ syllabusId = null, onSyllabusSelect = null }) {
  const toastRef = useRef(null);
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
  const [showAddTaskDialog, setShowAddTaskDialog] = useState(false);
  const [addingTask, setAddingTask] = useState(false);

  // Fetch available syllabuses on component mount
  useEffect(() => {
    if (!syllabusId) {
      fetchSyllabuses();
    } else {
      setSelectedSyllabus({ id: syllabusId });
    }
  }, [syllabusId]);

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

      if (!response.ok) {
        throw new Error('Failed to fetch syllabuses');
      }

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

      if (!response.ok) {
        throw new Error('Failed to fetch hierarchy data');
      }

      const result = await response.json();
      if (result.success && result.data.units) {
        setHierarchyData(result.data);
        toastRef.current?.show({
          severity: 'success',
          summary: 'Hierarchy Loaded',
          detail: `Loaded ${result.data.total_units} units with ${result.data.total_concepts} concepts`,
          life: 2000
        });
        if (onSyllabusSelect) {
          onSyllabusSelect(selectedSyllabus);
        }
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

  // Reset dependent selections when parent changes
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

    if (selectedTopic && selectedUnit && hierarchyData) {
      const unit = hierarchyData.units.find(u => u.unit_id === selectedUnit.unit_id);
      if (unit) {
        const topic = unit.topics.find(t => t.topic_id === selectedTopic);
        if (topic) {
          const concepts = topic.concepts.map(c => ({
            label: `${c.concept_name} (${c.complexity_level})`,
            value: c.id,
            complexity: c.complexity_level,
            name: c.concept_name
          }));
          setConceptOptions(concepts);
        }
      }
    }
  }, [selectedTopic, selectedUnit, hierarchyData]);

  const handleSyllabusSelect = (e) => {
    setSelectedSyllabus(e.value);
    // Reset hierarchy and selections when changing syllabus
    setHierarchyData(null);
    setSelectedUnit(null);
    setSelectedTopic(null);
    setSelectedConcepts([]);
    setTopicOptions([]);
    setConceptOptions([]);
    
    if (e.value) {
      toastRef.current?.show({
        severity: 'info',
        summary: 'Syllabus Selected',
        detail: `${e.value.course_name} selected`,
        life: 2000
      });
    }
  };

  const handleUnitChange = (e) => {
    setSelectedUnit(e.value);
    if (e.value?.unit_name) {
      toastRef.current?.show({
        severity: 'info',
        summary: 'Unit Selected',
        detail: `${e.value.unit_name} selected`,
        life: 2000
      });
    }
  };

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

  const handleConceptsChange = (e) => {
    setSelectedConcepts(e.value);
    if (e.value?.length > 0) {
      const conceptNames = e.value
        .map(id => {
          const concept = conceptOptions.find(c => c.value === id);
          return concept?.name;
        })
        .filter(Boolean)
        .join(', ');
      toastRef.current?.show({
        severity: 'info',
        summary: 'Concepts Updated',
        detail: `Selected: ${conceptNames}`,
        life: 2000
      });
    }
  };

  const handleAddToTask = async () => {
    try {
      setAddingTask(true);
      const token = localStorage.getItem('token');
      
      // Check if all requirements are met
      if (!selectedUnit?.unit_id || !selectedTopic || !selectedConcepts.length) {
        throw new Error('Please select unit, topic, and at least one concept');
      }

      // Prepare concepts data
      const conceptsToAdd = selectedConcepts.map(id => {
        const concept = conceptOptions.find(c => c.value === id);
        return {
          id: concept?.value,
          name: concept?.name,
          complexity: concept?.complexity
        };
      });

      const taskPayload = {
        syllabus_id: selectedSyllabus?.id,
        unit_id: selectedUnit?.unit_id,
        unit_name: selectedUnit?.unit_name || 'Unit',
        topic_id: selectedTopic,
        topic_name: topicOptions.find(t => t.value === selectedTopic)?.label,
        concepts: conceptsToAdd,
        start_date: new Date().toISOString(),
        description: `Learning task for ${topicOptions.find(t => t.value === selectedTopic)?.label}`
      };

      const response = await fetch('http://localhost:8000/tasks/from-concepts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(taskPayload)
      });

      if (!response.ok) {
        throw new Error('Failed to create task');
      }

      const result = await response.json();
      
      if (result.success) {
        toastRef.current?.show({
          severity: 'success',
          summary: '✓ Task Created',
          detail: `Task created successfully! Effort: ${result.data.effort_hours}h, End Date: ${new Date(result.data.end_date).toLocaleDateString()}`,
          life: 4000
        });
        setShowAddTaskDialog(false);
      } else {
        throw new Error(result.message || 'Failed to create task');
      }
    } catch (error) {
      console.error('Error adding task:', error);
      toastRef.current?.show({
        severity: 'error',
        summary: 'Error',
        detail: error.message || 'Failed to create task',
        life: 3000
      });
    } finally {
      setAddingTask(false);
    }
  };

  const handleLoadHierarchy = () => {
    fetchHierarchyData();
  };

  const unitOptions = hierarchyData?.units
    ?.filter(u => u && u.unit_name)
    ?.map(u => ({
      label: u.unit_name,
      value: {
        unit_id: u.unit_id,
        unit_name: u.unit_name
      }
    })) || [];

  const syllabusOptions = syllabuses.map(s => ({
    label: `${s.course_name} (${s.file_type})`,
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
          <h3>Select Unit & Concepts</h3>
          {selectedSyllabus && hierarchyData && (
            <p className="text-sm text-gray-600">
              {hierarchyData.course_name} | Units: {hierarchyData.total_units} | Topics: {hierarchyData.total_topics} | Concepts: {hierarchyData.total_concepts}
            </p>
          )}
          {!selectedSyllabus && (
            <p className="text-sm text-gray-600">
              Select a syllabus to begin
            </p>
          )}
        </div>

        {!selectedSyllabus || !hierarchyData ? (
          <div className="syllabus-selection-section">
            {/* Syllabus Selection */}
            <div className="form-group">
              <label htmlFor="syllabus-select">Step 1: Select a Syllabus *</label>
              <div className="input-group">
                <Dropdown
                  id="syllabus-select"
                  placeholder="Choose a syllabus..."
                  options={syllabusOptions}
                  value={selectedSyllabus}
                  onChange={handleSyllabusSelect}
                  className="w-full"
                  optionLabel="label"
                  loading={loadingSyllabuses}
                  disabled={loadingSyllabuses || syllabuses.length === 0}
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
                {topicOptions.length === 0 && selectedUnit && (
                  <small className="text-red-600">No topics available for this unit</small>
                )}
              </div>
            )}

            {selectedTopic && (
              <div className="form-group">
                <label htmlFor="concepts-select">Step 5: Select Concepts *</label>
                <MultiSelect
                  id="concepts-select"
                  placeholder="Select concepts"
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
                {conceptOptions.length === 0 && selectedTopic && (
                  <small className="text-red-600">No concepts available for this topic</small>
                )}
              </div>
            )}

            {selectedUnit && selectedTopic && selectedConcepts.length > 0 && (
              <div className="selection-summary">
                <div className="summary-card">
                  <div className="summary-header">
                    <h4>Selection Summary</h4>
                    <span className="concept-count-badge">{selectedConcepts.length} Concept{selectedConcepts.length !== 1 ? 's' : ''}</span>
                  </div>
                  
                  <div className="summary-meta">
                    <div className="meta-item">
                      <span className="meta-label">Syllabus</span>
                      <span className="meta-value">{selectedSyllabus?.course_name}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Unit</span>
                      <span className="meta-value">{selectedUnit?.unit_name || '-'}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Topic</span>
                      <span className="meta-value">{topicOptions.find(t => t.value === selectedTopic)?.label}</span>
                    </div>
                  </div>

                  <div className="concepts-divider"></div>

                  <div className="concepts-section">
                    <h5 className="concepts-title">Selected Concepts</h5>
                    <DataTable 
                      value={selectedConcepts.map(id => {
                        const concept = conceptOptions.find(c => c.value === id);
                        return {
                          name: concept?.name,
                          complexity: concept?.complexity,
                          color: getComplexityColor(concept?.complexity)
                        };
                      })}
                      className="summary-table"
                      size="small"
                      rowClassName={(rowData) => `summary-row complexity-${rowData.complexity?.toLowerCase()}`}
                    >
                      <Column 
                        field="name" 
                        header="Concept Name" 
                        style={{ width: '70%' }}
                        body={(rowData) => (
                          <span className="concept-name">{rowData.name}</span>
                        )}
                      />
                      <Column 
                        field="complexity" 
                        header="Level" 
                        style={{ width: '30%' }}
                        body={(rowData) => (
                          <span
                            className={`complexity-badge complexity-${rowData.complexity?.toLowerCase()}`}
                            style={{
                              backgroundColor: rowData.color
                            }}
                          >
                            {rowData.complexity}
                          </span>
                        )}
                      />
                    </DataTable>
                  </div>
                </div>
              </div>
            )}

            {/* Change Syllabus Button */}
            <div className="change-syllabus-section">
              <div className="button-group">
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
                
                {selectedUnit && selectedTopic && selectedConcepts.length > 0 && (
                  <Button
                    label="Add to Task"
                    icon="pi pi-plus"
                    onClick={() => setShowAddTaskDialog(true)}
                    className="p-button-success p-button-sm"
                  />
                )}
              </div>
            </div>
            
            {/* Add to Task Dialog */}
            <Dialog
              visible={showAddTaskDialog}
              onHide={() => setShowAddTaskDialog(false)}
              header="Create Task"
              modal
              maximizable
              style={{ width: '50vw' }}
              breakpoints={{ '960px': '75vw', '640px': '90vw' }}
            >
              <div className="add-task-dialog-content">
                <div className="task-summary">
                  <h4>Task Summary</h4>
                  <div className="task-meta">
                    <p><strong>Syllabus:</strong> {selectedSyllabus?.course_name}</p>
                    <p><strong>Unit:</strong> {selectedUnit?.unit_name || '-'}</p>
                    <p><strong>Topic:</strong> {topicOptions.find(t => t.value === selectedTopic)?.label}</p>
                    <p><strong>Concepts:</strong> {selectedConcepts.length}</p>
                  </div>
                </div>
                
                <div className="dialog-actions">
                  <Button
                    label="Cancel"
                    icon="pi pi-times"
                    onClick={() => setShowAddTaskDialog(false)}
                    className="p-button-secondary"
                  />
                  <Button
                    label="Create Task"
                    icon="pi pi-check"
                    onClick={handleAddToTask}
                    loading={addingTask}
                    className="p-button-success"
                  />
                </div>
              </div>
            </Dialog>
          </div>
        )}
      </Card>
    </div>
  );
}
