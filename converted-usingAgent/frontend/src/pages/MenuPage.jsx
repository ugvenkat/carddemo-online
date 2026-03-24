import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

const MenuPage = () => {
  const navigate = useNavigate();
  const [option, setOption] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [menuOptions, setMenuOptions] = useState([]);
  const [trnName, setTrnName] = useState('');
  const [pgmName, setPgmName] = useState('');
  const [title01, setTitle01] = useState('');
  const [title02, setTitle02] = useState('');

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
      width: '30px',
      textAlign: 'right'
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
      display: 'flex',
      gap: '4px'
    },
    centerSection: {
      flex: 1,
      textAlign: 'center'
    },
    rightSection: {
      display: 'flex',
      gap: '4px'
    },
    menuTitle: {
      textAlign: 'center',
      marginTop: '20px',
      marginBottom: '20px',
      fontWeight: 'bold'
    },
    menuOption: {
      paddingLeft: '150px',
      color: '#4488ff',
      cursor: 'pointer',
      marginBottom: '2px'
    },
    menuOptionHover: {
      textDecoration: 'underline'
    },
    promptRow: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      marginTop: '40px',
      gap: '8px'
    },
    errorRow: {
      marginTop: '40px'
    }
  };

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchMenuData = async () => {
      setLoading(true);
      try {
        const commArea = api.session.getCommArea();
        const result = await api.menu.post(commArea);
        if (result.data) {
          setTrnName(result.data.transactionName || 'MENU');
          setPgmName(result.data.programName || 'COMEN01C');
          setTitle01(result.data.title01 || 'CardDemo');
          setTitle02(result.data.title02 || 'Main Menu');
          setMenuOptions(result.data.menuOptions || [
            '01. View Account',
            '02. View Statement',
            '03. View Transaction',
            '04. Credit Card Bill Payment',
            '05. Update Account Information',
            '06. Generate Account Statement',
            '07. Reports',
            '08. Sign Off'
          ]);
        }
      } catch (err) {
        setErrorMsg(err.message || 'Error loading menu');
      } finally {
        setLoading(false);
      }
    };
    fetchMenuData();
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
    if (e) e.preventDefault();
    if (!option || option.trim() === '') {
      setErrorMsg('Please enter an option number');
      return;
    }
    const optionNum = parseInt(option, 10);
    if (isNaN(optionNum) || optionNum < 1 || optionNum > menuOptions.length) {
      setErrorMsg(`Invalid option. Please select 1-${menuOptions.length}`);
      return;
    }
    setLoading(true);
    setErrorMsg('');
    try {
      const commArea = api.session.getCommArea();
      const result = await api.menu.select(optionNum, commArea);
      if (result.success) {
        if (result.commArea) {
          api.session.saveCommArea(result.commArea);
        }
        if (result.redirect) {
          // Map COBOL program names to React routes
          const routeMap = {
            'COTRN00C': '/transactions',
            'COTRN01C': '/transactions',
            'COTRN02C': '/transactions/add',
            'COACTVWC': '/menu',
            'COACTUPC': '/menu',
            'COSTMTC':  '/menu',
            'COCRDLIC': '/menu',
            'COBIL00C': '/menu',
            'CORPT00C': '/menu',
            'COUSR00C': '/menu',
            'COSGN00C': '/login',
            '/api/transactions': '/transactions',
            '/api/accounts/view': '/menu',
          };
          const route = routeMap[result.redirect] || '/menu';
          navigate(route);
        }
      } else {
          // success - no error to show
      }
    } catch (err) {
      setErrorMsg(err.message || 'Error processing selection');
    } finally {
      setLoading(false);
    }
  };

  const handleOptionClick = (index) => {
    const optionNum = String(index + 1).padStart(2, '0');
    setOption(optionNum);
    setTimeout(() => handleSubmit(), 0);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === 'F3') {
      e.preventDefault();
      navigate('/signoff');
    }
  };

  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if (e.key === 'F3') {
        e.preventDefault();
        navigate('/signoff');
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [navigate]);

  return (
    <div style={styles.screen} onKeyDown={handleKeyDown}>
      <div style={styles.row}>
        <div style={styles.leftSection}>
          <span style={{ color: '#4488ff' }}>Tran:</span>
          <span style={{ color: '#4488ff' }}>{trnName}</span>
        </div>
        <div style={styles.centerSection}>
          <span style={styles.title}>{title01}</span>
        </div>
        <div style={styles.rightSection}>
          <span style={{ color: '#4488ff' }}>Date:</span>
          <span style={{ color: '#4488ff' }}>{formatDate(currentTime)}</span>
        </div>
      </div>

      <div style={styles.row}>
        <div style={styles.leftSection}>
          <span style={{ color: '#4488ff' }}>Prog:</span>
          <span style={{ color: '#4488ff' }}>{pgmName}</span>
        </div>
        <div style={styles.centerSection}>
          <span style={styles.title}>{title02}</span>
        </div>
        <div style={styles.rightSection}>
          <span style={{ color: '#4488ff' }}>Time:</span>
          <span style={{ color: '#4488ff' }}>{formatTime(currentTime)}</span>
        </div>
      </div>

      <div style={styles.menuTitle}>
        <span>Main Menu</span>
      </div>

      <div style={{ marginTop: '20px' }}>
        {menuOptions.map((opt, index) => (
          <div
            key={index}
            style={styles.menuOption}
            onClick={() => handleOptionClick(index)}
            onMouseEnter={(e) => e.target.style.textDecoration = 'underline'}
            onMouseLeave={(e) => e.target.style.textDecoration = 'none'}
          >
            {opt}
          </div>
        ))}
        {Array.from({ length: 12 - menuOptions.length }).map((_, index) => (
          <div key={`empty-${index}`} style={{ ...styles.menuOption, visibility: 'hidden' }}>
            &nbsp;
          </div>
        ))}
      </div>

      <div style={styles.promptRow}>
        <span style={styles.label}>Please select an option :</span>
        <input
          type="text"
          value={option}
          onChange={(e) => {
            const val = e.target.value.replace(/[^0-9]/g, '');
            if (val.length <= 2) setOption(val);
          }}
          onKeyDown={handleKeyDown}
          style={styles.input}
          maxLength={2}
          autoFocus
          disabled={loading}
        />
      </div>

      <div style={{ ...styles.errorRow, minHeight: '20px' }}>
        <span style={styles.error}>{errorMsg}</span>
      </div>

      <div style={styles.fkeyBar}>
        <span>ENTER=Continue  F3=Exit</span>
      </div>
    </div>
  );
};

export default MenuPage;
