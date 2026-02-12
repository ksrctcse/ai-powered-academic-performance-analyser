
import { Dropdown } from 'primereact/dropdown';
import { MultiSelect } from 'primereact/multiselect';

export default function UnitConceptSelector() {
  return (
    <div>
      <Dropdown placeholder="Select Unit" />
      <MultiSelect placeholder="Select Concepts" />
    </div>
  );
}
