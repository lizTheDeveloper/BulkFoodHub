import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken
          });
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Cart API functions
export const cartApi = {
  getCart: () => api.get('/api/v1/cart/'),
  addItem: (productId: number, quantity: number) => 
    api.post('/api/v1/cart/items/', { product_id: productId, quantity }),
  updateItem: (itemId: string, quantity: number) => 
    api.put(`/api/v1/cart/items/${itemId}`, { quantity }),
  removeItem: (itemId: string) => 
    api.delete(`/api/v1/cart/items/${itemId}`),
  clearCart: () => api.delete('/api/v1/cart/'),
};

// Orders API functions
export const ordersApi = {
  calculateOrder: (checkoutData: any) => 
    api.post('/api/v1/orders/calculate', checkoutData),
  createOrder: (checkoutData: any) => 
    api.post('/api/v1/orders/', checkoutData),
  getOrders: (skip = 0, limit = 100) => 
    api.get(`/api/v1/orders/?skip=${skip}&limit=${limit}`),
  getOrder: (orderId: string) => 
    api.get(`/api/v1/orders/${orderId}`),
};

export default api;
