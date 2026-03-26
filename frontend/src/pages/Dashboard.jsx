import { useState, useRef } from 'react';
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
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const [isNavbarCollapsed, setIsNavbarCollapsed] = useState(false);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [notificationCount] = useState(3);
  const [stats, setStats] = useState({
    totalTasks: 0,
    completedTasks: 0,
    inProgressTasks: 0,
    performancePercentage: 0,
  });
  const isStaff = user?.userType === 'staff';

  const renderContent = () => {
    switch (activeSection) {
      case 'dashboard':
        return (
          <section className="section-content">
            <h2>Dashboard</h2>
            <div className="dashboard-cards">
              <div className="stat-card">
                <div className="stat-icon">
                  <i className="pi pi-chart-bar"></i>
                </div>
                <div className="stat-info">
                  <h3>Total Tasks</h3>
                  <p className="stat-value">{stats.totalTasks}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <i className="pi pi-check-circle"></i>
                </div>
                <div className="stat-info">
                  <h3>Completed</h3>
                  <p className="stat-value">{stats.completedTasks}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <i className="pi pi-clock"></i>
                </div>
                <div className="stat-info">
                  <h3>In Progress</h3>
                  <p className="stat-value">{stats.inProgressTasks}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">
                  <i className="pi pi-star"></i>
                </div>
                <div className="stat-info">
                  <h3>Performance</h3>
                  <p className="stat-value">{stats.performancePercentage}%</p>
                </div>
              </div>
            </div>
          </section>
        );
      case 'upload-syllabus':
        return (
          <section className="section-content">
            <SyllabusUpload />
          </section>
        );
      case 'select-concepts':
        return (
          <section className="section-content">
            <h2>Select Unit & Concepts</h2>
            <UnitConceptSelector />
          </section>
        );
      case 'generate-tasks':
        return (
          <section className="section-content">
            <h2>Generate Tasks</h2>
            <TaskGenerator />
          </section>
        );
      case 'tasks':
        return (
          <section className="section-content">
            <TasksList />
          </section>
        );
      case 'view-tasks':
        return (
          <section className="section-content">
            <h2>Your Tasks</h2>
            <div className="tasks-list">
              <p>Student task list will be displayed here.</p>
            </div>
          </section>
        );
      default:
        return null;
    }
  };

  return (
    <div className="dashboard-layout">
      <Navbar
        user={user}
        onLogout={onLogout}
        isCollapsed={isNavbarCollapsed}
        setIsCollapsed={setIsNavbarCollapsed}
        activeSection={activeSection}
        setActiveSection={setActiveSection}
      />
      <Toast ref={toastRef} position="top-right" />

      <div className={`dashboard-main ${isNavbarCollapsed ? 'navbar-collapsed' : ''}`}>
        <header className="dashboard-header">
          <div className="header-content">
            <div>
              <h1>AI Academic Performance Analyser</h1>
              <p>{isStaff ? 'Staff Portal' : 'Student Portal'}</p>
            </div>
          </div>
          <div className="header-actions">
            <span className="user-greeting">Welcome, {user?.name || 'User'}</span>
            <Button
              icon="pi pi-fw pi-bell"
              className="p-button-text notification-icon-btn"
              badge={notificationCount}
              badgeClassName="p-badge-danger"
              tooltip="View Notifications"
              tooltipPosition="bottom"
            />
            <Button
              icon="pi pi-fw pi-sign-out"
              className="p-button-text header-logout-btn"
              onClick={onLogout}
              tooltip="Logout"
              tooltipPosition="bottom"
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
