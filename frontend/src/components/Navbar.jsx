import { Button } from 'primereact/button';
import './Navbar.css';

export default function Navbar({ user, onLogout, isCollapsed, setIsCollapsed, activeSection, setActiveSection }) {
  const isStaff = user?.userType === 'staff';

  const staffMenuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'pi pi-fw pi-chart-bar' },
    { id: 'upload-syllabus', label: 'Upload Syllabus', icon: 'pi pi-fw pi-upload' },
    { id: 'select-concepts', label: 'Select Unit & Concepts', icon: 'pi pi-fw pi-list' },
    { id: 'generate-tasks', label: 'Generate Tasks', icon: 'pi pi-fw pi-star' },
  ];

  const studentMenuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'pi pi-fw pi-chart-bar' },
    { id: 'view-tasks', label: 'View Tasks', icon: 'pi pi-fw pi-list' },
  ];

  const menuItems = isStaff ? staffMenuItems : studentMenuItems;

  return (
    <div className={`navbar-container ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Header with Hamburger */}
      <div className="navbar-header">
        <Button
          icon={isCollapsed ? 'pi pi-chevron-right' : 'pi pi-chevron-left'}
          className="p-button-text hamburger-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          tooltip={isCollapsed ? 'Expand' : 'Collapse'}
          tooltipPosition="right"
        />
        {!isCollapsed && (
          <h2 className="navbar-title">
            <i className="pi pi-fw pi-book" style={{ marginRight: '0.5rem' }}></i>
            AI Academy
          </h2>
        )}
      </div>

      {/* Navigation Menu */}
      <nav className="navbar-menu">
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`navbar-menu-item ${activeSection === item.id ? 'active' : ''}`}
            onClick={() => setActiveSection(item.id)}
            title={isCollapsed ? item.label : ''}
          >
            <i className={item.icon}></i>
            {!isCollapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Empty footer to push menu up */}
      <div className="navbar-footer-spacer"></div>
    </div>
  );
}
