import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './Dashboard';
import Login from './Login';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsAuthenticated(!!token);
    setLoading(false);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        Loading...
      </div>
    );
  }

  return (
    <Routes>

      {/* LOGIN */}
      <Route 
        path="/login" 
        element={
          isAuthenticated 
          ? <Navigate to="/dashboard" /> 
          : <Login onLoginSuccess={handleLoginSuccess} />
        } 
      />

      {/* DASHBOARD ROUTES */}
      <Route 
        path="/dashboard" 
        element={
          isAuthenticated 
          ? <Dashboard onLogout={handleLogout} /> 
          : <Navigate to="/login" />
        } 
      />

      <Route 
        path="/upload-Syllabus" 
        element={
          isAuthenticated 
          ? <Dashboard onLogout={handleLogout} /> 
          : <Navigate to="/login" />
        } 
      />

      <Route 
        path="/concepts" 
        element={
          isAuthenticated 
          ? <Dashboard onLogout={handleLogout} /> 
          : <Navigate to="/login" />
        } 
      />

      <Route 
        path="/generate-tasks" 
        element={
          isAuthenticated 
          ? <Dashboard onLogout={handleLogout} /> 
          : <Navigate to="/login" />
        } 
      />

      <Route 
        path="/tasks" 
        element={
          isAuthenticated 
          ? <Dashboard onLogout={handleLogout} /> 
          : <Navigate to="/login" />
        } 
      />

      {/* DEFAULT */}
      <Route path="/" element={<Navigate to="/login" />} />

    </Routes>
  );
}