import { useRef, useState } from 'react';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import api from '../api/api';

export default function TaskGenerator() {
  const toastRef = useRef(null);
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const response = await api.post('/tasks/generate', { concept: 'Normalization' });
      toastRef.current?.show({ severity: 'success', summary: 'Success', detail: 'Tasks generated successfully', life: 3000 });
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate tasks';
      toastRef.current?.show({ severity: 'error', summary: 'Error', detail: errorMessage, life: 3000 });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Toast ref={toastRef} position="top-right" />
      <Button
        label="Generate Tasks"
        onClick={generate}
        loading={loading}
        className="p-button-lg"
      />
    </>
  );
}
