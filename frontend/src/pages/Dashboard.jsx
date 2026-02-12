
import UnitConceptSelector from '../components/UnitConceptSelector';
import TaskGenerator from '../components/TaskGenerator';

export default function Dashboard() {
  return (
    <div>
      <h2>Staff Dashboard</h2>
      <UnitConceptSelector />
      <TaskGenerator />
    </div>
  );
}
