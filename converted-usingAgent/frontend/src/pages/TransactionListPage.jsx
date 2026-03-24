import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

const TransactionListPage = () => {
  const navigate = useNavigate();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [searchTranId, setSearchTranId] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [selections, setSelections] = useState(['', '', '', '', '', '', '', '', '', '']);
  const [pageNum, setPageNum] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

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
    row: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      minHeight: '20px'
    },
    leftSection: {
      display: 'flex',
      alignItems: 'center'
    },
    centerSection: {
      flex: 1,
      textAlign: 'center'
    },
    rightSection: {
      display: 'flex',
      alignItems: 'center'
    },
    labelBlue: {
      color: '#4488ff'
    },
    valueBlue: {
      color: '#4488ff'
    },
    titleYellow: {
      color: '#ffff00'
    },
    labelTurquoise: {
      color: '#00ffff'
    },
    input: {
      background: 'transparent',
      border: 'none',
      borderBottom: '1px solid #00ff00',
      color: '#00ff00',
      fontFamily: 'inherit',
      fontSize: 'inherit',
      outline: 'none',
      padding: '0 4px'
    },
    selInput: {
      background: 'transparent',
      border: 'none',
      borderBottom: '1px solid #00ff00',
      color: '#00ff00',
      fontFamily: 'inherit',
      fontSize: 'inherit',
      outline: 'none',
      padding: '0',
      width: '20px',
      textAlign: 'center'
    },
    titleBright: {
      color: '#ffffff',
      fontWeight: 'bold'
    },
    tableHeader: {
      color: '#cccccc',
      display: 'flex',
      alignItems: 'center',
      marginTop: '16px'
    },
    tableRow: {
      display: 'flex',
      alignItems: 'center',
      minHeight: '20px'
    },
    colSel: {
      width: '40px',
      textAlign: 'center'
    },
    colTranId: {
      width: '160px',
      paddingLeft: '8px',
      overflow: 'hidden'
    },
    colDate: {
      width: '80px',
      paddingLeft: '12px'
    },
    colDesc: {
      width: '220px'
    },
    colAmount: {
      width: '110px',
      textAlign: 'right'
    },
    separator: {
      color: '#cccccc'
    },
    error: {
      color: '#ff0000',
      fontWeight: 'bold',
      minHeight: '20px'
    },
    fkeyBar: {
      color: '#ffff00',
      borderTop: '1px solid #444',
      paddingTop: '4px',
      marginTop: '8px'
    },
    instruction: {
      color: '#ffffff',
      textAlign: 'center',
      marginTop: '16px'
    },
    clickableRow: {
      cursor: 'pointer'
    }
  };

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchTransactions();
  }, [pageNum]);

  const fetchTransactions = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      const commArea = api.session.getCommArea();
      const params = { page: pageNum, pageSize: 10 };
      if (searchTranId.trim()) {
        params.tranId = searchTranId.trim();
      }
      const result = await api.transactions.list(pageNum);
      if (result.success) {
        setTransactions(result.data?.transactions || []);
        setTotalPages(result.data?.hasNextPage ? pageNum + 1 : pageNum);
        setSelections(['', '', '', '', '', '', '', '', '', '']);
      } else {
        if (!result.success) setErrorMsg(result.message || 'Failed to fetch transactions');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Error fetching transactions');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPageNum(1);
    fetchTransactions();
  };

  const handleSelectionChange = (index, value) => {
    const newSelections = [...selections];
    newSelections[index] = value.toUpperCase();
    setSelections(newSelections);
  };

  const handleSelectionKeyDown = (e, index) => {
    if (e.key === 'Enter') {
      const selection = selections[index];
      if (selection === 'S' && transactions[index]) {
        navigate(`/transactions/${transactions[index].tranId}`);
      }
    }
  };

  const handleRowClick = (transaction) => {
    if (transaction && transaction.tranId) {
      navigate(`/transactions/${transaction.tranId}`);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'F3') {
      e.preventDefault();
      navigate(-1);
    } else if (e.key === 'F7') {
      e.preventDefault();
      if (pageNum > 1) {
        setPageNum(pageNum - 1);
      }
    } else if (e.key === 'F8') {
      e.preventDefault();
      if (pageNum < totalPages) {
        setPageNum(pageNum + 1);
      }
    }
  };

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [pageNum, totalPages]);

  const formatDate = (date) => {
    if (!date) return '        ';
    const d = new Date(date);
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const yy = String(d.getFullYear()).slice(-2);
    return `${mm}/${dd}/${yy}`;
  };

  const formatTime = (date) => {
    const hh = String(date.getHours()).padStart(2, '0');
    const mm = String(date.getMinutes()).padStart(2, '0');
    const ss = String(date.getSeconds()).padStart(2, '0');
    return `${hh}:${mm}:${ss}`;
  };

  const formatAmount = (amount) => {
    if (amount === undefined || amount === null) return '            ';
    return Number(amount).toFixed(2).padStart(12, ' ');
  };

  const renderTransactionRow = (index) => {
    const transaction = transactions[index] || {};
    const rowNum = String(index + 1).padStart(2, '0');
    
    return (
      <div 
        key={index} 
        style={{...styles.tableRow, ...styles.clickableRow}}
        onClick={() => handleRowClick(transaction)}
      >
        <div style={styles.colSel}>
          <input
            type="text"
            style={styles.selInput}
            value={selections[index]}
            onChange={(e) => handleSelectionChange(index, e.target.value)}
            onKeyDown={(e) => handleSelectionKeyDown(e, index)}
            maxLength={1}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
        <div style={{...styles.colTranId, ...styles.valueBlue}}>
          {transaction.tranId || ''}
        </div>
        <div style={{...styles.colDate, ...styles.valueBlue}}>
          {transaction.tranDate ? formatDate(transaction.tranDate) : ''}
        </div>
        <div style={{...styles.colDesc, ...styles.valueBlue}}>
          {transaction.tranDesc || ''}
        </div>
        <div style={{...styles.colAmount, ...styles.valueBlue}}>
          {transaction.tranAmt !== undefined ? formatAmount(transaction.tranAmt) : ''}
        </div>
      </div>
    );
  };

  return (
    <div style={styles.screen}>
      {/* Row 1 */}
      <div style={styles.row}>
        <div style={styles.leftSection}>
          <span style={styles.labelBlue}>Tran:</span>
          <span style={{...styles.valueBlue, marginLeft: '4px'}}>COTR</span>
        </div>
        <div style={styles.centerSection}>
          <span style={styles.titleYellow}>CardDemo - Transaction List</span>
        </div>
        <div style={styles.rightSection}>
          <span style={styles.labelBlue}>Date:</span>
          <span style={{...styles.valueBlue, marginLeft: '4px'}}>
            {formatDate(currentTime)}
          </span>
        </div>
      </div>

      {/* Row 2 */}
      <div style={styles.row}>
        <div style={styles.leftSection}>
          <span style={styles.labelBlue}>Prog:</span>
          <span style={{...styles.valueBlue, marginLeft: '4px'}}>COTRN00C</span>
        </div>
        <div style={styles.centerSection}>
          <span style={styles.titleYellow}></span>
        </div>
        <div style={styles.rightSection}>
          <span style={styles.labelBlue}>Time:</span>
          <span style={{...styles.valueBlue, marginLeft: '4px'}}>
            {formatTime(currentTime)}
          </span>
        </div>
      </div>

      {/* Row 4 - Title and Page */}
      <div style={{...styles.row, marginTop: '16px'}}>
        <div style={{flex: 1}}></div>
        <div style={styles.centerSection}>
          <span style={styles.titleBright}>List Transactions</span>
        </div>
        <div style={styles.rightSection}>
          <span style={styles.labelTurquoise}>Page:</span>
          <span style={{...styles.valueBlue, marginLeft: '4px'}}>
            {String(pageNum).padStart(3, ' ')} of {totalPages}
          </span>
        </div>
      </div>

      {/* Row 6 - Search */}
      <div style={{...styles.row, marginTop: '16px', justifyContent: 'flex-start'}}>
        <span style={{...styles.labelTurquoise, marginLeft: '32px'}}>Search Tran ID:</span>
        <form onSubmit={handleSearch} style={{display: 'inline'}}>
          <input
            type="text"
            style={{...styles.input, width: '140px', marginLeft: '4px'}}
            value={searchTranId}
            onChange={(e) => setSearchTranId(e.target.value)}
            maxLength={16}
            autoFocus
          />
        </form>
      </div>

      {/* Row 8 - Table Header */}
      <div style={{...styles.tableHeader, marginTop: '16px'}}>
        <div style={styles.colSel}>Sel</div>
        <div style={styles.colTranId}> Transaction ID </div>
        <div style={styles.colDate}>  Date  </div>
        <div style={styles.colDesc}>     Description          </div>
        <div style={styles.colAmount}>   Amount   </div>
      </div>

      {/* Row 9 - Separator */}
      <div style={{...styles.separator, display: 'flex'}}>
        <div style={styles.colSel}>---</div>
        <div style={styles.colTranId}>----------------</div>
        <div style={styles.colDate}>--------</div>
        <div style={styles.colDesc}>--------------------------</div>
        <div style={styles.colAmount}>------------</div>
      </div>

      {/* Rows 10-19 - Transaction Data */}
      {loading ? (
        <div style={{color: '#ffff00', textAlign: 'center', marginTop: '20px'}}>
          Loading transactions...
        </div>
      ) : (
        <>
          {renderTransactionRow(0)}
          {renderTransactionRow(1)}
          {renderTransactionRow(2)}
          {renderTransactionRow(3)}
          {renderTransactionRow(4)}
          {renderTransactionRow(5)}
          {renderTransactionRow(6)}
          {renderTransactionRow(7)}
          {renderTransactionRow(8)}
          {renderTransactionRow(9)}
        </>
      )}

      {/* Row 21 - Instructions */}
      <div style={styles.instruction}>
        Type 'S' to View Transaction details from the list
      </div>

      {/* Row 23 - Error Message */}
      <div style={{...styles.error, marginTop: '16px', minHeight: '20px'}}>
        {errorMsg}
      </div>

      {/* Row 24 - Function Keys */}
      <div style={styles.fkeyBar}>
        ENTER=Continue  F3=Back  F7=Backward  F8=Forward
      </div>
    </div>
  );
};

export default TransactionListPage;
