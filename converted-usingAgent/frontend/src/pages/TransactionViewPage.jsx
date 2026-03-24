import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

const TransactionViewPage = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  
  const [currentTime, setCurrentTime] = useState(new Date());
  const [trnIdIn, setTrnIdIn] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  const [transaction, setTransaction] = useState({
    trnId: '',
    cardNum: '',
    ttypCd: '',
    tcatCd: '',
    trnSrc: '',
    tDesc: '',
    trnAmt: '',
    tOrigDt: '',
    tProcDt: '',
    mid: '',
    mName: '',
    mCity: '',
    mZip: ''
  });

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (id) {
      setTrnIdIn(id);
      fetchTransaction(id);
    }
  }, [id]);

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

  const fetchTransaction = async (transactionId) => {
    if (!transactionId || transactionId.trim() === '') {
      setErrorMsg('Transaction ID is required');
      return;
    }
    
    setLoading(true);
    setErrorMsg('');
    
    try {
      const commArea = api.session.getCommArea();
      const result = await api.transactions.get(transactionId.trim());
      
      if (result.success) {
        setTransaction({
          trnId: result.data.tranId || '',
          cardNum: result.data.cardNum || '',
          ttypCd: result.data.tranTypeCd || '',
          tcatCd: result.data.tranCatCd || '',
          trnSrc: result.data.tranSource || '',
          tDesc: result.data.tranDesc || '',
          trnAmt: result.data.tranAmt || '',
          tOrigDt: result.data.tranOrigTs || '',
          tProcDt: result.data.tranProcTs || '',
          mid: result.data.merchantId || '',
          mName: result.data.merchantName || '',
          mCity: result.data.merchantCity || '',
          mZip: result.data.merchantZip || ''
        });
        if (result.commArea) {
          api.session.saveCommArea(result.commArea);
        }
      } else {
        setErrorMsg(result.message || 'Transaction not found');
        clearTransactionData();
      }
    } catch (err) {
      setErrorMsg(err.message || 'Error fetching transaction');
      clearTransactionData();
    } finally {
      setLoading(false);
    }
  };

  const clearTransactionData = () => {
    setTransaction({
      trnId: '',
      cardNum: '',
      ttypCd: '',
      tcatCd: '',
      trnSrc: '',
      tDesc: '',
      trnAmt: '',
      tOrigDt: '',
      tProcDt: '',
      mid: '',
      mName: '',
      mCity: '',
      mZip: ''
    });
  };

  const handleClear = () => {
    setTrnIdIn('');
    setErrorMsg('');
    clearTransactionData();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchTransaction(trnIdIn);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'F3') {
      e.preventDefault();
      navigate(-1);
    } else if (e.key === 'F4') {
      e.preventDefault();
      handleClear();
    } else if (e.key === 'F5') {
      e.preventDefault();
      navigate('/transactions');
    }
  };

  const styles = {
    screen: {
      backgroundColor: '#000033',
      color: '#00ff00',
      fontFamily: 'Courier New, monospace',
      fontSize: '14px',
      minHeight: '100vh',
      padding: '8px',
      boxSizing: 'border-box'
    },
    row: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      minHeight: '20px',
      lineHeight: '20px'
    },
    headerLeft: {
      display: 'flex',
      alignItems: 'center'
    },
    headerCenter: {
      flex: 1,
      textAlign: 'center'
    },
    headerRight: {
      display: 'flex',
      alignItems: 'center'
    },
    labelBlue: {
      color: '#4488ff'
    },
    valueBlue: {
      color: '#4488ff'
    },
    title: {
      color: '#ffff00'
    },
    sectionTitle: {
      color: '#cccccc',
      fontWeight: 'bold',
      textAlign: 'center',
      marginTop: '20px',
      marginBottom: '10px'
    },
    label: {
      color: '#00ffff'
    },
    display: {
      color: '#4488ff'
    },
    input: {
      backgroundColor: 'transparent',
      border: 'none',
      borderBottom: '1px solid #00ff00',
      color: '#00ff00',
      fontFamily: 'Courier New, monospace',
      fontSize: '14px',
      outline: 'none',
      padding: '0 4px',
      width: '160px'
    },
    separator: {
      color: '#cccccc',
      margin: '10px 0'
    },
    fieldRow: {
      display: 'flex',
      alignItems: 'center',
      minHeight: '24px',
      marginBottom: '4px'
    },
    fieldGroup: {
      display: 'flex',
      alignItems: 'center',
      marginRight: '20px'
    },
    error: {
      color: '#ff0000',
      fontWeight: 'bold',
      minHeight: '20px',
      marginTop: '20px'
    },
    fkeyBar: {
      color: '#ffff00',
      borderTop: '1px solid #444444',
      paddingTop: '4px',
      marginTop: '8px',
      position: 'fixed',
      bottom: '8px',
      left: '8px',
      right: '8px'
    },
    button: {
      backgroundColor: '#004400',
      color: '#00ff00',
      border: '1px solid #00ff00',
      fontFamily: 'Courier New, monospace',
      fontSize: '12px',
      padding: '2px 8px',
      cursor: 'pointer',
      marginLeft: '10px'
    }
  };

  return (
    <div style={styles.screen} onKeyDown={handleKeyDown} tabIndex={0}>
      <div style={styles.row}>
        <div style={styles.headerLeft}>
          <span style={styles.labelBlue}>Tran:</span>
          <span style={styles.valueBlue}> COTR</span>
        </div>
        <div style={styles.headerCenter}>
          <span style={styles.title}>CardDemo - Transaction View</span>
        </div>
        <div style={styles.headerRight}>
          <span style={styles.labelBlue}>Date:</span>
          <span style={styles.valueBlue}> {formatDate(currentTime)}</span>
        </div>
      </div>

      <div style={styles.row}>
        <div style={styles.headerLeft}>
          <span style={styles.labelBlue}>Prog:</span>
          <span style={styles.valueBlue}> COTRN01C</span>
        </div>
        <div style={styles.headerCenter}>
          <span style={styles.title}></span>
        </div>
        <div style={styles.headerRight}>
          <span style={styles.labelBlue}>Time:</span>
          <span style={styles.valueBlue}> {formatTime(currentTime)}</span>
        </div>
      </div>

      <div style={styles.sectionTitle}>View Transaction</div>

      <form onSubmit={handleSubmit}>
        <div style={{ ...styles.fieldRow, marginTop: '20px' }}>
          <span style={styles.label}>Enter Tran ID:</span>
          <input
            type="text"
            style={styles.input}
            value={trnIdIn}
            onChange={(e) => setTrnIdIn(e.target.value)}
            maxLength={16}
            autoFocus
          />
          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? 'Loading...' : 'Fetch'}
          </button>
        </div>
      </form>

      <div style={styles.separator}>
        {'─'.repeat(70)}
      </div>

      <div style={styles.fieldRow}>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Transaction ID:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '160px' }}>{transaction.trnId}</span>
        </div>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Card Number:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '160px' }}>{transaction.cardNum}</span>
        </div>
      </div>

      <div style={{ ...styles.fieldRow, marginTop: '16px' }}>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Type CD:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '20px' }}>{transaction.ttypCd}</span>
        </div>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Category CD:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '40px' }}>{transaction.tcatCd}</span>
        </div>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Source:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '100px' }}>{transaction.trnSrc}</span>
        </div>
      </div>

      <div style={{ ...styles.fieldRow, marginTop: '16px' }}>
        <span style={styles.label}>Description:</span>
        <span style={{ ...styles.display, marginLeft: '8px', minWidth: '600px' }}>{transaction.tDesc}</span>
      </div>

      <div style={{ ...styles.fieldRow, marginTop: '16px' }}>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Amount:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '120px' }}>{transaction.trnAmt}</span>
        </div>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Orig Date:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '100px' }}>{transaction.tOrigDt}</span>
        </div>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Proc Date:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '100px' }}>{transaction.tProcDt}</span>
        </div>
      </div>

      <div style={{ ...styles.fieldRow, marginTop: '16px' }}>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Merchant ID:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '90px' }}>{transaction.mid}</span>
        </div>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Merchant Name:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '300px' }}>{transaction.mName}</span>
        </div>
      </div>

      <div style={{ ...styles.fieldRow, marginTop: '16px' }}>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Merchant City:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '250px' }}>{transaction.mCity}</span>
        </div>
        <div style={styles.fieldGroup}>
          <span style={styles.label}>Merchant Zip:</span>
          <span style={{ ...styles.display, marginLeft: '8px', minWidth: '100px' }}>{transaction.mZip}</span>
        </div>
      </div>

      <div style={styles.error}>{errorMsg}</div>

      <div style={styles.fkeyBar}>
        ENTER=Fetch  F3=Back  F4=Clear  F5=Browse Tran.
      </div>
    </div>
  );
};

export default TransactionViewPage;