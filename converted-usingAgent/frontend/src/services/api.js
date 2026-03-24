const BASE_URL = 'http://localhost:8080';

const api = {
  auth: {
    async login(userId, password) {
      console.log('API Request: POST /api/auth/login', { userId });
      const response = await fetch(`${BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userId, password }),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async logout() {
      console.log('API Request: POST /api/auth/logout');
      const response = await fetch(`${BASE_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async getScreen() {
      console.log('API Request: GET /api/auth/screen');
      const response = await fetch(`${BASE_URL}/api/auth/screen`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },
  },

  menu: {
    async get() {
      console.log('API Request: GET /api/menu');
      const response = await fetch(`${BASE_URL}/api/menu`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async post(commArea) {
      console.log('API Request: POST /api/menu', { commArea });
      const response = await fetch(`${BASE_URL}/api/menu`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(commArea),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async select(option, commArea) {
      console.log('API Request: POST /api/menu/select', { option, commArea });
      const response = await fetch(`${BASE_URL}/api/menu/select`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ option, commArea }),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },
  },

  transactions: {
    async list(page = 1) {
      console.log('API Request: GET /api/transactions', { page });
      const response = await fetch(`${BASE_URL}/api/transactions?page=${page}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async get(id) {
      console.log('API Request: GET /api/transactions/:id', { id });
      const response = await fetch(`${BASE_URL}/api/transactions/${id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async getAddForm() {
      console.log('API Request: GET /api/transactions/add');
      const response = await fetch(`${BASE_URL}/api/transactions/add`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async add(transaction) {
      console.log('API Request: POST /api/transactions', { transaction });
      const response = await fetch(`${BASE_URL}/api/transactions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transaction),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async select(tranId, commArea) {
      console.log('API Request: POST /api/transactions/select', { tranId, commArea });
      const response = await fetch(`${BASE_URL}/api/transactions/select`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ tranId, commArea }),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },

    async copy(cardNumber) {
      console.log('API Request: POST /api/transactions/copy', { cardNumber });
      const response = await fetch(`${BASE_URL}/api/transactions/copy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ cardNumber }),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message);
      return data;
    },
  },

  session: {
    getCommArea() {
      const commArea = localStorage.getItem('commArea');
      return commArea ? JSON.parse(commArea) : null;
    },

    saveCommArea(commArea) {
      localStorage.setItem('commArea', JSON.stringify(commArea));
    },

    clearCommArea() {
      localStorage.removeItem('commArea');
    },
  },
};

export default api;