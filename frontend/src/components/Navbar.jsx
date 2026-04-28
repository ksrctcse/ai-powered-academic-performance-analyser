import { Button } from 'primereact/button';
import { useNavigate } from "react-router-dom"; // ✅ ADDED
import './Navbar.css';

export default function Navbar({ user, onLogout, isCollapsed, setIsCollapsed, currentPath }) {

  const navigate = useNavigate(); // ✅ ADDED
  const isStaff = user?.userType === 'staff';

  const staffMenuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: 'pi pi-fw pi-chart-bar' },
    { path: '/upload-Syllabus', label: 'Upload Syllabus', icon: 'pi pi-fw pi-upload' },
    { path: '/concepts', label: 'Select Unit & Concepts', icon: 'pi pi-fw pi-list' },
    { path: '/generate-tasks', label: 'Generate Tasks', icon: 'pi pi-fw pi-star' },
    { path: '/tasks', label: 'Tasks', icon: 'pi pi-fw pi-check-square' },
  ];

  const studentMenuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: 'pi pi-fw pi-chart-bar' },
    { path: '/tasks', label: 'View Tasks', icon: 'pi pi-fw pi-list' },
  ];

  const menuItems = isStaff ? staffMenuItems : studentMenuItems;

  return (
    <div className={`navbar-container ${isCollapsed ? 'collapsed' : ''}`}>

      {/* Header */}
      <div className="navbar-header">
        <Button
          icon={isCollapsed ? 'pi pi-chevron-right' : 'pi pi-chevron-left'}
          className="p-button-text hamburger-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
        />
        {!isCollapsed && <h2 className="navbar-title">AI Academy</h2>}
      </div>

      {/* ✅ FIXED MENU */}
      <nav className="navbar-menu">
        {menuItems.map((item) => (
          <button
            key={item.path}
            className={`navbar-menu-item ${currentPath === item.path ? 'active' : ''}`}
            onClick={() => navigate(item.path)}   // ✅ FIXED
            title={isCollapsed ? item.label : ''}
          >
            <i className={item.icon}></i>
            {!isCollapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>

      <div className="navbar-footer-spacer"></div>
    </div>
  );
}