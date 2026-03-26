import React, { useState, useRef } from 'react';
import { Card } from 'primereact/card';
import { InputText } from 'primereact/inputtext';
import { Password } from 'primereact/password';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { TabView, TabPanel } from 'primereact/tabview';
import { Dropdown } from 'primereact/dropdown';
import PasswordStrength from '../components/PasswordStrength';
import api from '../api/api';
import './Login.css';

export default function Login({ onLoginSuccess }) {
  const toastRef = useRef(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loadingLogin, setLoadingLogin] = useState(false);
  const [loadingSignup, setLoadingSignup] = useState(false);

  const departmentOptions = [
    { label: 'Computer Science & Engineering', value: 'CSE' },
    { label: 'Information Technology', value: 'IT' },
    { label: 'Electronics & Communication', value: 'ECE' },
    { label: 'Electrical & Electronics', value: 'EEE' }
  ];

  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
    userType: 'staff' // 'staff' or 'student'
  });

  const [staffSignupData, setStaffSignupData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    department: ''
  });

  const [studentSignupData, setStudentSignupData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    rollNumber: '',
    department: ''
  });

  const handleLoginChange = (e) => {
    const { name, value } = e.target;
    setLoginData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleStaffSignupChange = (e) => {
    const { name, value } = e.target;
    setStaffSignupData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleStudentSignupChange = (e) => {
    const { name, value } = e.target;
    setStudentSignupData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const validateLogin = () => {
    if (!loginData.email.trim()) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Email is required', life: 3000 });
      return false;
    }
    if (!loginData.password) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Password is required', life: 3000 });
      return false;
    }
    return true;
  };

  const validateSignup = (isStaff) => {
    const data = isStaff ? staffSignupData : studentSignupData;
    
    if (!data.email.trim()) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Email is required', life: 3000 });
      return false;
    }
    if (!data.password) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Password is required', life: 3000 });
      return false;
    }
    if (!data.name.trim()) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Name is required', life: 3000 });
      return false;
    }
    if (!isStaff && !data.rollNumber.trim()) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Roll Number is required', life: 3000 });
      return false;
    }
    if (!data.department) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Department is required', life: 3000 });
      return false;
    }
    if (data.password.length < 6) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Password must be at least 6 characters', life: 3000 });
      return false;
    }
    if (data.password !== data.confirmPassword) {
      toastRef.current?.show({ severity: 'error', summary: 'Validation Error', detail: 'Passwords do not match', life: 3000 });
      return false;
    }
    return true;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!validateLogin()) return;

    setLoadingLogin(true);

    try {
      console.log(`[Login Component] Login attempt for email: ${loginData.email}`);
      
      const response = await api.post('/auth/login', {
        email: loginData.email,
        password: loginData.password
      });
      
      console.log('[Login Component] Login successful', response.data);
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      toastRef.current?.show({ severity: 'success', summary: 'Login Successful', detail: 'Welcome back!', life: 3000 });
      setTimeout(() => onLoginSuccess(), 500);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Login failed';
      console.error('[Login Component] Login error:', {
        timestamp: new Date().toISOString(),
        error: errorMessage,
        status: err.response?.status
      });
      toastRef.current?.show({ severity: 'error', summary: 'Login Failed', detail: errorMessage, life: 3000 });
    } finally {
      setLoadingLogin(false);
    }
  };

  const handleStaffSignup = async (e) => {
    e.preventDefault();
    
    if (!validateSignup(true)) return;

    setLoadingSignup(true);

    try {
      console.log(`[Login Component] Staff signup attempt for email: ${staffSignupData.email}`);
      
      const response = await api.post('/auth/signup', {
        email: staffSignupData.email,
        password: staffSignupData.password,
        name: staffSignupData.name,
        department: staffSignupData.department,
        userType: 'staff'
      });
      
      console.log('[Login Component] Staff signup successful', response.data);
      toastRef.current?.show({ severity: 'success', summary: 'Signup Successful', detail: 'Account created! Please login.', life: 3000 });
      setStaffSignupData({
        email: '',
        password: '',
        confirmPassword: '',
        name: '',
        department: ''
      });
      setTimeout(() => setActiveTab(0), 500);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Signup failed';
      console.error('[Login Component] Staff signup error:', {
        timestamp: new Date().toISOString(),
        error: errorMessage,
        status: err.response?.status
      });
      toastRef.current?.show({ severity: 'error', summary: 'Signup Failed', detail: errorMessage, life: 3000 });
    } finally {
      setLoadingSignup(false);
    }
  };

  const handleStudentSignup = async (e) => {
    e.preventDefault();
    
    if (!validateSignup(false)) return;

    setLoadingSignup(true);

    try {
      console.log(`[Login Component] Student signup attempt for email: ${studentSignupData.email}`);
      
      const response = await api.post('/auth/signup', {
        email: studentSignupData.email,
        password: studentSignupData.password,
        name: studentSignupData.name,
        rollNumber: studentSignupData.rollNumber,
        department: studentSignupData.department,
        userType: 'student'
      });
      
      console.log('[Login Component] Student signup successful', response.data);
      toastRef.current?.show({ severity: 'success', summary: 'Signup Successful', detail: 'Account created! Please login.', life: 3000 });
      setStudentSignupData({
        email: '',
        password: '',
        confirmPassword: '',
        name: '',
        rollNumber: '',
        department: ''
      });
      setTimeout(() => setActiveTab(0), 500);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Signup failed';
      console.error('[Login Component] Student signup error:', {
        timestamp: new Date().toISOString(),
        error: errorMessage,
        status: err.response?.status
      });
      toastRef.current?.show({ severity: 'error', summary: 'Signup Failed', detail: errorMessage, life: 3000 });
    } finally {
      setLoadingSignup(false);
    }
  };

  return (
    <div className="login-container">
      <Toast ref={toastRef} position="top-right" />
      <div className="login-content">
        <div className="login-header">
          <div className="logo-section">
            <i className="pi pi-book" style={{ fontSize: '3rem' }}></i>
          </div>
          <h1 className="page-title">AI Academic Performance</h1>
          <p className="page-subtitle">Analyser Platform</p>
          <p className="page-description">Empowering Academic Excellence Through Intelligent Analysis</p>
        </div>

        <div className="login-wrapper">
          <Card className="login-card">
          <TabView activeIndex={activeTab} onTabChange={(e) => setActiveTab(e.index)}>
            {/* Login Tab */}
            <TabPanel header="Login" leftIcon="pi pi-fw pi-sign-in">
              <form onSubmit={handleLogin}>
                <div className="form-group">
                  <label htmlFor="login-email">Email</label>
                  <InputText
                    id="login-email"
                    name="email"
                    type="email"
                    value={loginData.email}
                    onChange={handleLoginChange}
                    placeholder="Enter your email"
                    className="w-full"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="login-password">Password</label>
                  <Password
                    id="login-password"
                    name="password"
                    value={loginData.password}
                    onChange={handleLoginChange}
                    placeholder="Enter your password"
                    toggleMask
                    className="w-full"
                  />
                </div>

                <div className="form-actions">
                  <Button
                    type="submit"
                    label="Login"
                    loading={loadingLogin}
                    className="w-full p-button-lg"
                  />
                </div>
              </form>
            </TabPanel>

            {/* Staff Sign Up Tab */}
            <TabPanel header="Staff Sign Up" leftIcon="pi pi-fw pi-user-plus">
              <form onSubmit={handleStaffSignup}>
                <div className="form-group">
                  <label htmlFor="staff-name">Full Name</label>
                  <InputText
                    id="staff-name"
                    name="name"
                    value={staffSignupData.name}
                    onChange={handleStaffSignupChange}
                    placeholder="Enter your full name"
                    className="w-full"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="staff-email">Email</label>
                  <InputText
                    id="staff-email"
                    name="email"
                    type="email"
                    value={staffSignupData.email}
                    onChange={handleStaffSignupChange}
                    placeholder="Enter your email"
                    className="w-full"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="staff-department">Department</label>
                  <Dropdown
                    id="staff-department"
                    name="department"
                    value={staffSignupData.department}
                    onChange={handleStaffSignupChange}
                    options={departmentOptions}
                    placeholder="Select your department"
                    className="w-full"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="staff-password">Password</label>
                  <Password
                    id="staff-password"
                    name="password"
                    value={staffSignupData.password}
                    onChange={handleStaffSignupChange}
                    placeholder="Enter your password (min. 6 characters)"
                    toggleMask
                    className="w-full"
                  />
                  <PasswordStrength password={staffSignupData.password} />
                </div>

                <div className="form-group">
                  <label htmlFor="staff-confirm-password">Confirm Password</label>
                  <Password
                    id="staff-confirm-password"
                    name="confirmPassword"
                    value={staffSignupData.confirmPassword}
                    onChange={handleStaffSignupChange}
                    placeholder="Confirm your password"
                    toggleMask
                    className="w-full"
                  />
                  {staffSignupData.confirmPassword && (
                    <div className="confirm-password-match">
                      {staffSignupData.password === staffSignupData.confirmPassword ? (
                        <span className="match-success">
                          <i className="pi pi-check" style={{ marginRight: '0.5rem' }}></i>
                          Passwords match
                        </span>
                      ) : (
                        <span className="match-error">
                          <i className="pi pi-times" style={{ marginRight: '0.5rem' }}></i>
                          Passwords do not match
                        </span>
                      )}
                    </div>
                  )}
                </div>

                <div className="form-actions">
                  <Button
                    type="submit"
                    label="Create Staff Account"
                    loading={loadingSignup}
                    className="w-full p-button-lg"
                  />
                </div>
              </form>
            </TabPanel>

            {/* Student Sign Up Tab */}
            <TabPanel header="Student Sign Up" leftIcon="pi pi-fw pi-id-card">
              <form onSubmit={handleStudentSignup}>
                <div className="form-group">
                  <label htmlFor="student-name">Full Name</label>
                  <InputText
                    id="student-name"
                    name="name"
                    value={studentSignupData.name}
                    onChange={handleStudentSignupChange}
                    placeholder="Enter your full name"
                    className="w-full"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="student-email">Email</label>
                  <InputText
                    id="student-email"
                    name="email"
                    type="email"
                    value={studentSignupData.email}
                    onChange={handleStudentSignupChange}
                    placeholder="Enter your email"
                    className="w-full"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="student-roll">Roll Number</label>
                  <InputText
                    id="student-roll"
                    name="rollNumber"
                    value={studentSignupData.rollNumber}
                    onChange={handleStudentSignupChange}
                    placeholder="Enter your roll number"
                    className="w-full"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="student-department">Department</label>
                  <Dropdown
                    id="student-department"
                    name="department"
                    value={studentSignupData.department}
                    onChange={handleStudentSignupChange}
                    options={departmentOptions}
                    placeholder="Select your department"
                    className="w-full"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="student-password">Password</label>
                  <Password
                    id="student-password"
                    name="password"
                    value={studentSignupData.password}
                    onChange={handleStudentSignupChange}
                    placeholder="Enter your password (min. 6 characters)"
                    toggleMask
                    className="w-full"
                  />
                  <PasswordStrength password={studentSignupData.password} />
                </div>

                <div className="form-group">
                  <label htmlFor="student-confirm-password">Confirm Password</label>
                  <Password
                    id="student-confirm-password"
                    name="confirmPassword"
                    value={studentSignupData.confirmPassword}
                    onChange={handleStudentSignupChange}
                    placeholder="Confirm your password"
                    toggleMask
                    className="w-full"
                  />
                  {studentSignupData.confirmPassword && (
                    <div className="confirm-password-match">
                      {studentSignupData.password === studentSignupData.confirmPassword ? (
                        <span className="match-success">
                          <i className="pi pi-check" style={{ marginRight: '0.5rem' }}></i>
                          Passwords match
                        </span>
                      ) : (
                        <span className="match-error">
                          <i className="pi pi-times" style={{ marginRight: '0.5rem' }}></i>
                          Passwords do not match
                        </span>
                      )}
                    </div>
                  )}
                </div>

                <div className="form-actions">
                  <Button
                    type="submit"
                    label="Create Student Account"
                    loading={loadingSignup}
                    className="w-full p-button-lg"
                  />
                </div>
              </form>
            </TabPanel>
          </TabView>
        </Card>
      </div>
    </div>
    </div>
  );
}
