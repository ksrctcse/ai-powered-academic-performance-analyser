import { useState, useRef } from 'react';
import { useNavigate, useLocation } from "react-router-dom"; // ✅ ADDED
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import Navbar from '../components/Navbar';
import SyllabusUpload from '../components/SyllabusUpload';
import UnitConceptSelector from '../components/UnitConceptSelector';
import TaskGenerator from '../components/TaskGenerator';
import TasksList from '../components/TasksList';
import './Dashboard.css';

export default function Dashboard({ onLogout }) {
  const toastRef = useRef(null);
  const navigate = useNavigate();       // ✅ ADDED
  const location = useLocation();       // ✅ ADDED

  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [isNavbarCollapsed, setIsNavbarCollapsed] = useState(false);
  const [notificationCount] = useState(3);

  const [stats, setStats] = useState({
    totalTasks: 0,
    completedTasks: 0,
    inProgressTasks: 0,
    performancePercentage: 0,
  });

  const isStaff = user?.userType === 'staff';

  // ✅ UPDATED ROUTING LOGIC
  const renderContent = () => {
    switch (location.pathname) {

      case '/dashboard':
        return (
          <section className="section-content">
            <h2>Dashboard</h2>
            <div className="dashboard-cards">
              <div className="stat-card">
                <i className="pi pi-chart-bar"></i>
                <h3>Total Tasks</h3>
                <p>{stats.totalTasks}</p>
              </div>
              <div className="stat-card">
                <i className="pi pi-check-circle"></i>
                <h3>Completed</h3>
                <p>{stats.completedTasks}</p>
              </div>
              <div className="stat-card">
                <i className="pi pi-clock"></i>
                <h3>In Progress</h3>
                <p>{stats.inProgressTasks}</p>
              </div>
              <div className="stat-card">
                <i className="pi pi-star"></i>
                <h3>Performance</h3>
                <p>{stats.performancePercentage}%</p>
              </div>
            </div>
          </section>
        );

      case '/upload':
        return (
          <section className="section-content">
            <SyllabusUpload />
          </section>
        );

      case '/concepts':
        return (
          <section className="section-content">
            <UnitConceptSelector />
          </section>
        );

      case '/generate':
        return (
          <section className="section-content">
            <TaskGenerator />
          </section>
        );

      case '/tasks':
        return (
          <section className="section-content">
            <TasksList />
          </section>
        );

      default:
        return (
          <section className="section-content">
            <h2>Dashboard</h2>
          </section>
        );
    }
  };

  return (
    <div className="dashboard-layout">

      {/* ✅ PASS NAVIGATE TO NAVBAR */}
      <Navbar
        user={user}
        onLogout={onLogout}
        isCollapsed={isNavbarCollapsed}
        setIsCollapsed={setIsNavbarCollapsed}
        navigate={navigate}                 // ✅ NEW
        currentPath={location.pathname}     // ✅ NEW
      />

      <Toast ref={toastRef} position="top-right" />

      <div className={`dashboard-main ${isNavbarCollapsed ? 'navbar-collapsed' : ''}`}>

        <header className="dashboard-header">
          <h1>AI Academic Performance Analyser</h1>
          <p>{isStaff ? 'Staff Portal' : 'Student Portal'}</p>

          <div>
            <span>Welcome, {user?.name}</span>

            <Button icon="pi pi-bell" badge={notificationCount} />

            <Button
              icon="pi pi-sign-out"
              size="small"
              onClick={onLogout}
            />
          </div>
        </header>

        <main className="dashboard-content">
          {renderContent()}
        </main>

      </div>
    </div>
  );
}