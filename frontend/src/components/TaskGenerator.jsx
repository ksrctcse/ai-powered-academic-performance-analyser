
import api from '../api/api';

export default function TaskGenerator() {
  const generate = async () => {
    await api.post('/tasks/generate', { concept: 'Normalization' });
  };
  return <button onClick={generate}>Generate Tasks</button>;
}
