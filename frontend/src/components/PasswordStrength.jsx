import React from 'react';
import './PasswordStrength.css';

export default function PasswordStrength({ password = '' }) {
  const calculateStrength = (pwd) => {
    if (!pwd) return 0;

    let strength = 0;

    // Length checks
    if (pwd.length >= 6) strength += 20;
    if (pwd.length >= 10) strength += 10;
    if (pwd.length >= 14) strength += 10;

    // Contains lowercase
    if (/[a-z]/.test(pwd)) strength += 15;

    // Contains uppercase
    if (/[A-Z]/.test(pwd)) strength += 15;

    // Contains numbers
    if (/[0-9]/.test(pwd)) strength += 15;

    // Contains special characters
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd)) strength += 15;

    return Math.min(strength, 100);
  };

  const getStrengthLabel = (strength) => {
    if (strength === 0) return 'No Password';
    if (strength < 25) return 'Very Weak';
    if (strength < 50) return 'Weak';
    if (strength < 75) return 'Good';
    if (strength < 90) return 'Strong';
    return 'Very Strong';
  };

  const getStrengthColor = (strength) => {
    if (strength === 0) return '#ccc';
    if (strength < 25) return '#d32f2f';
    if (strength < 50) return '#ff9800';
    if (strength < 75) return '#ffc107';
    if (strength < 90) return '#90caf9';
    return '#4caf50';
  };

  const strength = calculateStrength(password);
  const label = getStrengthLabel(strength);
  const color = getStrengthColor(strength);

  return (
    <div className="password-strength-container">
      <div className="password-strength-bar">
        <div
          className="password-strength-fill"
          style={{
            width: `${strength}%`,
            backgroundColor: color
          }}
        ></div>
      </div>
      <span className="password-strength-label" style={{ color }}>
        {label}
      </span>
    </div>
  );
}
