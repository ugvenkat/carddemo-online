import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

const TransactionAddPage = () => {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  
  const [acctId, setAcctId] = useState('');
  const [cardNum, setCardNum] = useState('');
  const [typeCode, setTypeCode] = useState('');
  const [categoryCode, setCategoryCode] = useState('');
  const [source, setSource] = useState('');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [origDate, setOrigDate] = useState('');
  const [procDate, setProcDate] = useState('');
  const [merchantId, setMerchantId] = useState('');
  const [merchantName, setMerchantName] = useState('');
  const [merchantCity, setMerchantCity] = useState('');
  const [merchantZip, setMerchantZip] = useState('');
  const [confirm, setConfirm] = useState('');
  
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

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

  const clearForm = () => {
    setAcctId('');
    setCardNum('');
    setTypeCode('');
    setCategoryCode('');
    setSource('');
    setDescription('');
    setAmount('');
    setOrigDate('');
    setProcDate('');
    setMerchantId('');
    setMerchantName('');
    setMerchantCity('');
    setMerchantZip('');
    setConfirm('');
    setErrorMsg('');
    setSuccessMsg('');
  };

  const copyLastTransaction = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const cardNumber = cardNum || acctId;
      if (!cardNumber) {
        setErrorMsg('Please enter Account ID or Card Number first');
        return;
      }
      const result = await api.transactions.copy(cardNumber);
      if (result.data) {
        const tran = result.data;
        setTypeCode(tran.typeCode || '');
        setCategoryCode(tran.categoryCode || '');
        setSource(tran.source || '');
        setDescription(tran.description || '');
        setAmount(tran.amount || '');
        setOrigDate(tran.origDate || '');
        setProcDate(tran.procDate || '');
        setMerchantId(tran.merchantId || '');
        setMerchantName(tran.merchantName || '');
        setMerchantCity(tran.merchantCity || '');
        setMerchantZip(tran.merchantZip || '');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to copy last transaction');
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    if (!acctId && !cardNum) {
      setErrorMsg('Enter Account ID or Card Number');
      return false;
    }
    if (!typeCode) {
      setErrorMsg('Type Code is required');
      return false;
    }
    if (!categoryCode) {
      setErrorMsg('Category Code is required');
      return false;
    }
    if (!amount) {
      setErrorMsg('Amount is required');
      return false;
    }
    const amountPattern = /^-?\d{1,8}(\.\d{1,2})?$/;
    if (!amountPattern.test(amount)) {
      setErrorMsg('Invalid Amount format. Use -99999999.99 format');
      return false;
    }
    if (origDate && !/^\d{4}-\d{2}-\d{2}$/.test(origDate)) {
      setErrorMsg('Invalid Orig Date format. Use YYYY-MM-DD');
      return false;
    }
    if (procDate && !/^\d{4}-\d{2}-\d{2}$/.test(procDate)) {
      setErrorMsg('Invalid Proc Date format. Use YYYY-MM-DD');
      return false;
    }
    if (confirm.toUpperCase() !== 'Y') {
      setErrorMsg('Please confirm with Y to add transaction');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    try {
      const commArea = api.session.getCommArea();
      const transactionData = {
        accountId: acctId,
        cardNumber: cardNum,
        typeCode: typeCode.toUpperCase(),
        categoryCode: categoryCode,
        source: source,
        description: description,
        amount: parseFloat(amount),
        origDate: origDate,
        procDate: procDate,
        merchantId: merchantId,
        merchantName: merchantName,
        merchantCity: merchantCity,
        merchantZip: merchantZip,
        commArea: commArea
      };
      
      const result = await api.transactions.add(transactionData);
      if (result.success) {
        setSuccessMsg(`Transaction added successfully. Transaction ID: ${result.transactionId}`);
        setErrorMsg('');
        setConfirm('');
      } else {
        setErrorMsg(result.message || 'Failed to add transaction');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Error adding transaction');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'F3' || (e.key === 'Escape')) {
      e.preventDefault();
      navigate(-1);
    } else if (e.key === 'F4') {
      e.preventDefault();
      clearForm();
    } else if (e.key === 'F5') {
      e.preventDefault();
      copyLastTransaction();
    }
  };

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [cardNum, acctId]);

  const styles = {
    screen: {
      backgroundColor: '#000033',
      color: '#00ff00',
      fontFamily: 'Courier New, monospace',
      minHeight: '100vh',
      padding: '8px',
      fontSize: '14px',
      lineHeight: '1.4'
    },
    row: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      minHeight: '20px'
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
    label: {
      color: '#4488ff'
    },
    value: {
      color: '#4488ff'
    },
    title: {
      color: '#ffff00'
    },
    screenTitle: {
      color: '#ffffff',
      fontWeight: 'bold',
      textAlign: 'center',
      marginTop: '16px',
      marginBottom: '8px'
    },
    fieldLabel: {
      color: '#00ffff'
    },
    input: {
      backgroundColor: 'transparent',
      border: 'none',
      borderBottom: '1px solid #00ff00',
      color: '#00ff00',
      fontFamily: 'Courier New, monospace',
      fontSize: '14px',
      outline: 'none',
      padding: '0 4px'
    },
    separator: {
      color: '#ffffff',
      margin: '8px 0'
    },
    hint: {
      color: '#4488ff',
      fontSize: '12px'
    },
    neutralText: {
      color: '#ffffff'
    },
    error: {
      color: '#ff0000',
      fontWeight: 'bold',
      minHeight: '20px'
    },
    success: {
      color: '#00ff00',
      fontWeight: 'bold',
      minHeight: '20px'
    },
    fkeyBar: {
      color: '#ffff00',
      borderTop: '1px solid #444444',
      paddingTop: '4px',
      marginTop: '8px'
    },
    formRow: {
      display: 'flex',
      alignItems: 'center',
      marginBottom: '8px',
      flexWrap: 'wrap'
    },
    formGroup: {
      display: 'flex',
      alignItems: 'center',
      marginRight: '16px'
    }
  };

  return (
    <div style={styles.screen}>
      <form onSubmit={handleSubmit}>
        {/* Header Row 1 */}
        <div style={styles.row}>
          <div style={styles.headerLeft}>
            <span style={styles.label}>Tran:</span>
            <span style={styles.value}>COTR</span>
          </div>
          <div style={styles.headerCenter}>
            <span style={styles.title}>CardDemo - Transaction Add</span>
          </div>
          <div style={styles.headerRight}>
            <span style={styles.label}>Date:</span>
            <span style={styles.value}>{formatDate(currentTime)}</span>
          </div>
        </div>

        {/* Header Row 2 */}
        <div style={styles.row}>
          <div style={styles.headerLeft}>
            <span style={styles.label}>Prog:</span>
            <span style={styles.value}>COTRN02C</span>
          </div>
          <div style={styles.headerCenter}>
            <span style={styles.title}></span>
          </div>
          <div style={styles.headerRight}>
            <span style={styles.label}>Time:</span>
            <span style={styles.value}>{formatTime(currentTime)}</span>
          </div>
        </div>

        {/* Screen Title */}
        <div style={styles.screenTitle}>Add Transaction</div>

        {/* Account/Card Input Row */}
        <div style={styles.formRow}>
          <span style={styles.fieldLabel}>Enter Acct #:</span>
          <input
            type="text"
            value={acctId}
            onChange={(e) => setAcctId(e.target.value)}
            maxLength={11}
            style={{ ...styles.input, width: '110px', marginLeft: '4px' }}
            autoFocus
          />
          <span style={{ ...styles.neutralText, marginLeft: '16px', marginRight: '16px' }}>(or)</span>
          <span style={styles.fieldLabel}>Card #:</span>
          <input
            type="text"
            value={cardNum}
            onChange={(e) => setCardNum(e.target.value)}
            maxLength={16}
            style={{ ...styles.input, width: '160px', marginLeft: '4px' }}
          />
        </div>

        {/* Separator Line */}
        <div style={styles.separator}>
          {'─'.repeat(70)}
        </div>

        {/* Type CD, Category CD, Source Row */}
        <div style={styles.formRow}>
          <span style={styles.fieldLabel}>Type CD:</span>
          <input
            type="text"
            value={typeCode}
            onChange={(e) => setTypeCode(e.target.value.toUpperCase())}
            maxLength={2}
            style={{ ...styles.input, width: '30px', marginLeft: '4px' }}
          />
          <span style={{ ...styles.fieldLabel, marginLeft: '24px' }}>Category CD:</span>
          <input
            type="text"
            value={categoryCode}
            onChange={(e) => setCategoryCode(e.target.value)}
            maxLength={4}
            style={{ ...styles.input, width: '50px', marginLeft: '4px' }}
          />
          <span style={{ ...styles.fieldLabel, marginLeft: '24px' }}>Source:</span>
          <input
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            maxLength={10}
            style={{ ...styles.input, width: '100px', marginLeft: '4px' }}
          />
        </div>

        {/* Description Row */}
        <div style={styles.formRow}>
          <span style={styles.fieldLabel}>Description:</span>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={60}
            style={{ ...styles.input, width: '480px', marginLeft: '4px' }}
          />
        </div>

        {/* Amount, Orig Date, Proc Date Row */}
        <div style={styles.formRow}>
          <span style={styles.fieldLabel}>Amount:</span>
          <input
            type="text"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            maxLength={12}
            style={{ ...styles.input, width: '120px', marginLeft: '4px' }}
          />
          <span style={{ ...styles.fieldLabel, marginLeft: '16px' }}>Orig Date:</span>
          <input
            type="text"
            value={origDate}
            onChange={(e) => setOrigDate(e.target.value)}
            maxLength={10}
            placeholder="YYYY-MM-DD"
            style={{ ...styles.input, width: '100px', marginLeft: '4px' }}
          />
          <span style={{ ...styles.fieldLabel, marginLeft: '16px' }}>Proc Date:</span>
          <input
            type="text"
            value={procDate}
            onChange={(e) => setProcDate(e.target.value)}
            maxLength={10}
            placeholder="YYYY-MM-DD"
            style={{ ...styles.input, width: '100px', marginLeft: '4px' }}
          />
        </div>

        {/* Format Hints Row */}
        <div style={styles.formRow}>
          <span style={{ ...styles.hint, marginLeft: '70px' }}>(-99999999.99)</span>
          <span style={{ ...styles.hint, marginLeft: '80px' }}>(YYYY-MM-DD)</span>
          <span style={{ ...styles.hint, marginLeft: '80px' }}>(YYYY-MM-DD)</span>
        </div>

        {/* Merchant ID, Merchant Name Row */}
        <div style={styles.formRow}>
          <span style={styles.fieldLabel}>Merchant ID:</span>
          <input
            type="text"
            value={merchantId}
            onChange={(e) => setMerchantId(e.target.value)}
            maxLength={9}
            style={{ ...styles.input, width: '90px', marginLeft: '4px' }}
          />
          <span style={{ ...styles.fieldLabel, marginLeft: '16px' }}>Merchant Name:</span>
          <input
            type="text"
            value={merchantName}
            onChange={(e) => setMerchantName(e.target.value)}
            maxLength={30}
            style={{ ...styles.input, width: '240px', marginLeft: '4px' }}
          />
        </div>

        {/* Merchant City, Merchant Zip Row */}
        <div style={styles.formRow}>
          <span style={styles.fieldLabel}>Merchant City:</span>
          <input
            type="text"
            value={merchantCity}
            onChange={(e) => setMerchantCity(e.target.value)}
            maxLength={25}
            style={{ ...styles.input, width: '200px', marginLeft: '4px' }}
          />
          <span style={{ ...styles.fieldLabel, marginLeft: '16px' }}>Merchant Zip:</span>
          <input
            type="text"
            value={merchantZip}
            onChange={(e) => setMerchantZip(e.target.value)}
            maxLength={10}
            style={{ ...styles.input, width: '100px', marginLeft: '4px' }}
          />
        </div>

        {/* Spacer */}
        <div style={{ marginTop: '24px' }}></div>

        {/* Confirmation Row */}
        <div style={styles.formRow}>
          <span style={styles.fieldLabel}>You are about to add this transaction. Please confirm :</span>
          <input
            type="text"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value.toUpperCase())}
            maxLength={1}
            style={{ ...styles.input, width: '20px', marginLeft: '4px' }}
          />
          <span style={{ ...styles.neutralText, marginLeft: '8px' }}>(Y/N)</span>
        </div>

        {/* Spacer */}
        <div style={{ marginTop: '16px' }}></div>

        {/* Error/Success Message Row */}
        <div style={styles.error}>
          {errorMsg}
        </div>
        <div style={styles.success}>
          {successMsg}
        </div>

        {/* Function Key Bar */}
        <div style={styles.fkeyBar}>
          ENTER=Continue  F3=Back  F4=Clear  F5=Copy Last Tran.
        </div>

        {/* Hidden submit button for Enter key */}
        <button type="submit" style={{ display: 'none' }} disabled={loading}>
          Submit
        </button>
      </form>
    </div>
  );
};

export default TransactionAddPage;