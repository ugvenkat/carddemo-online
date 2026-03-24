import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import MenuPage from './pages/MenuPage';
import TransactionListPage from './pages/TransactionListPage';
import TransactionViewPage from './pages/TransactionViewPage';
import TransactionAddPage from './pages/TransactionAddPage';
import api from './services/api';

function Navbar() {
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());
  const commArea = api.session.getCommArea();

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <nav className="terminal-navbar">
      <span className="navbar-brand">CardDemo</span>
      <span className="navbar-user" style={{marginRight: "12px"}}> User: {commArea?.cdemoUserId || 'N/A'}</span>
      <span className="navbar-time">{currentTime}</span>
    </nav>
  );
}

function ProtectedRoute() {
  const commArea = api.session.getCommArea();

  if (!commArea) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="terminal-container">
      <Navbar />
      <main className="terminal-main">
        <Outlet />
      </main>
    </div>
  );
}

function App() {
  return (
    <div className="terminal-app dark-terminal">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/menu" element={<MenuPage />} />
            <Route path="/transactions" element={<TransactionListPage />} />
            <Route path="/transactions/add" element={<TransactionAddPage />} />
            <Route path="/transactions/:id" element={<TransactionViewPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
