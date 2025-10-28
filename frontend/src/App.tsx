import React from 'react';
import { Router } from './Router';
import { CartProvider } from './contexts/CartContext';
import './App.css';

function App() {
  return (
    <CartProvider>
      <div className="App">
        <Router />
      </div>
    </CartProvider>
  );
}

export default App;
