import { useRef, useState } from 'react';
import { Dropdown } from 'primereact/dropdown';
import { MultiSelect } from 'primereact/multiselect';
import { Toast } from 'primereact/toast';

export default function UnitConceptSelector() {
  const toastRef = useRef(null);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [selectedConcepts, setSelectedConcepts] = useState([]);

  const units = [
    { label: 'Unit 1: Basics', value: 'unit1' },
    { label: 'Unit 2: Advanced', value: 'unit2' },
    { label: 'Unit 3: Expert', value: 'unit3' }
  ];

  const concepts = [
    { label: 'Concept A', value: 'conceptA' },
    { label: 'Concept B', value: 'conceptB' },
    { label: 'Concept C', value: 'conceptC' },
    { label: 'Concept D', value: 'conceptD' }
  ];

  const handleUnitChange = (e) => {
    setSelectedUnit(e.value);
    if (e.value) {
      toastRef.current?.show({ severity: 'info', summary: 'Unit Selected', detail: `${e.value} selected`, life: 2000 });
    }
  };

  const handleConceptsChange = (e) => {
    setSelectedConcepts(e.value);
    if (e.value?.length > 0) {
      toastRef.current?.show({ severity: 'info', summary: 'Concepts Updated', detail: `${e.value.length} concept(s) selected`, life: 2000 });
    }
  };

  return (
    <div className="unit-concept-selector">
      <Toast ref={toastRef} position="top-right" />
      <Dropdown
        placeholder="Select Unit"
        options={units}
        value={selectedUnit}
        onChange={handleUnitChange}
        className="w-full mb-3"
      />
      <MultiSelect
        placeholder="Select Concepts"
        options={concepts}
        value={selectedConcepts}
        onChange={handleConceptsChange}
        className="w-full"
      />
    </div>
  );
}
