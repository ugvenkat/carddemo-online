import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

const LoginPage = () => {
  const navigate = useNavigate();
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  const styles = {
    screen: {
      background: '#000033',
      color: '#00ff00',
      fontFamily: 'Courier New, monospace',
      minHeight: '100vh',
      padding: '8px',
      fontSize: '14px',
      lineHeight: '1.4'
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      color: '#4488ff'
    },
    title: {
      color: '#ffff00',
      textAlign: 'center'
    },
    label: {
      color: '#00ffff'
    },
    input: {
      background: 'transparent',
      border: 'none',
      borderBottom: '1px solid #00ff00',
      color: '#00ff00',
      fontFamily: 'inherit',
      outline: 'none',
      padding: '0 4px',
      fontSize: '14px',
      width: '80px'
    },
    error: {
      color: '#ff0000',
      fontWeight: 'bold'
    },
    fkeyBar: {
      color: '#ffff00',
      borderTop: '1px solid #444',
      paddingTop: '4px',
      marginTop: '8px'
    },
    row: {
      display: 'flex',
      justifyContent: 'space-between',
      marginBottom: '2px'
    },
    leftSection: {
      color: '#4488ff'
    },
    centerSection: {
      color: '#ffff00',
      flex: 1,
      textAlign: 'center'
    },
    rightSection: {
      color: '#4488ff',
      textAlign: 'right'
    },
    asciiArt: {
      color: '#4488ff',
      textAlign: 'center',
      margin: '20px 0'
    },
    description: {
      color: '#a0a0a0',
      textAlign: 'center',
      margin: '10px 0'
    },
    formContainer: {
      textAlign: 'center',
      marginTop: '20px'
    },
    formRow: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      margin: '8px 0'
    },
    formLabel: {
      color: '#00ffff',
      width: '120px',
      textAlign: 'right',
      marginRight: '10px'
    },
    hint: {
      color: '#4488ff',
      marginLeft: '10px'
    },
    prompt: {
      color: '#00ffff',
      textAlign: 'center',
      margin: '20px 0'
    }
  };

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatDate = (date) => {
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const yy = String(date.getFullYear()).slice(-2);
    return `${mm}/${dd}/${yy}`;
  };

  const formatTime = (date) => {
    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    const ss = String(date.getSeconds()).padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    try {
      const result = await api.auth.login(userId, password);
      if (result.success) {
        api.session.saveCommArea(result.commArea);
        // Navigate to menu regardless of admin/user — menu handles access control
        navigate('/menu');
      } else {
        setErrorMsg(result.message);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'F3') {
      e.preventDefault();
      navigate(-1);
    } else if (e.key === 'F4') {
      e.preventDefault();
      setUserId('');
      setPassword('');
      setErrorMsg('');
    }
  };

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const creditCardArt = `+========================================+
|%%%%%%%  NATIONAL RESERVE NOTE  %%%%%%%%|
|%(1)  THE UNITED STATES OF KICSLAND (1)%|
|%$$              ___       ********  $$%|
|%$    {x}       (o o)                 $%|
|%$     ******  (  V  )      O N E     $%|
|%(1)          ---m-m---             (1)%|
|%%~~~~~~~~~~~ ONE DOLLAR ~~~~~~~~~~~~~%%|
+========================================+`;

  return (
    <div style={styles.screen} onKeyDown={handleKeyDown}>
      {/* Header Row 1 */}
      <div style={styles.row}>
        <div style={styles.leftSection}>
          <span>Tran : </span>
          <span>CSGN</span>
        </div>
        <div style={styles.centerSection}>
          <span style={styles.title}>CardDemo - Sign On</span>
        </div>
        <div style={styles.rightSection}>
          <span>Date : </span>
          <span>{formatDate(currentTime)}</span>
        </div>
      </div>

      {/* Header Row 2 */}
      <div style={styles.row}>
        <div style={styles.leftSection}>
          <span>Prog : </span>
          <span>COSGN00C</span>
        </div>
        <div style={styles.centerSection}>
          <span style={styles.title}>Sign On Screen</span>
        </div>
        <div style={styles.rightSection}>
          <span>Time : </span>
          <span>{formatTime(currentTime)}</span>
        </div>
      </div>

      {/* Header Row 3 */}
      <div style={styles.row}>
        <div style={styles.leftSection}>
          <span>AppID: </span>
          <span>CARDDEMO</span>
        </div>
        <div style={styles.centerSection}></div>
        <div style={styles.rightSection}>
          <span>SysID: </span>
          <span>CICS</span>
        </div>
      </div>

      {/* Description */}
      <div style={styles.description}>
        This is a Credit Card Demo Application for Mainframe Modernization
      </div>

      {/* ASCII Art Credit Card */}
      <pre style={styles.asciiArt}>{creditCardArt}</pre>

      {/* Login Prompt */}
      <div style={styles.prompt}>
        Type your User ID and Password, then press ENTER:
      </div>

      {/* Login Form */}
      <form onSubmit={handleSubmit} style={styles.formContainer}>
        <div style={styles.formRow}>
          <span style={styles.formLabel}>User ID     :</span>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value.toUpperCase())}
            maxLength={8}
            autoFocus
            style={styles.input}
            disabled={loading}
          />
          <span style={styles.hint}>(8 Char)</span>
        </div>

        <div style={styles.formRow}>
          <span style={styles.formLabel}>Password    :</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            maxLength={8}
            style={styles.input}
            disabled={loading}
          />
          <span style={styles.hint}>(8 Char)</span>
        </div>

        <button type="submit" style={{ display: 'none' }} disabled={loading}>
          Submit
        </button>
      </form>

      {/* Spacer */}
      <div style={{ flex: 1, minHeight: '60px' }}></div>

      {/* Error Message Row 23 */}
      <div style={{ ...styles.error, minHeight: '20px', marginTop: '20px' }}>
        {errorMsg}
        {loading && <span style={{ color: '#00ff00' }}>Processing...</span>}
      </div>

      {/* Function Key Bar Row 24 */}
      <div style={styles.fkeyBar}>
        ENTER=Sign-on  F3=Exit
      </div>
    </div>
  );
};

export default LoginPage;