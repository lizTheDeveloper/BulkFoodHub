import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { Product, CartItem } from '../types';

interface CartState {
  items: CartItem[];
  totalItems: number;
  totalPrice: number;
}

type CartAction =
  | { type: 'ADD_ITEM'; payload: { product: Product; quantity: number } }
  | { type: 'REMOVE_ITEM'; payload: { productId: number } }
  | { type: 'UPDATE_QUANTITY'; payload: { productId: number; quantity: number } }
  | { type: 'CLEAR_CART' };

interface CartContextType {
  state: CartState;
  addItem: (product: Product, quantity: number) => void;
  removeItem: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  clearCart: () => void;
  getItemQuantity: (productId: number) => number;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

const cartReducer = (state: CartState, action: CartAction): CartState => {
  switch (action.type) {
    case 'ADD_ITEM': {
      const { product, quantity } = action.payload;
      const existingItem = state.items.find(item => item.product.id === product.id);
      
      if (existingItem) {
        const updatedItems = state.items.map(item =>
          item.product.id === product.id
            ? {
                ...item,
                quantity: item.quantity + quantity,
                total_price: (item.quantity + quantity) * item.unit_price,
              }
            : item
        );
        
        return {
          ...state,
          items: updatedItems,
          totalItems: state.totalItems + quantity,
          totalPrice: updatedItems.reduce((sum, item) => sum + item.total_price, 0),
        };
      } else {
        const newItem: CartItem = {
          id: `${product.id}-${Date.now()}`,
          product,
          quantity,
          unit_price: product.price_per_unit,
          total_price: product.price_per_unit * quantity,
          added_at: new Date().toISOString(),
        };
        
        return {
          ...state,
          items: [...state.items, newItem],
          totalItems: state.totalItems + quantity,
          totalPrice: state.totalPrice + newItem.total_price,
        };
      }
    }
    
    case 'REMOVE_ITEM': {
      const itemToRemove = state.items.find(item => item.product.id === action.payload.productId);
      if (!itemToRemove) return state;
      
      const updatedItems = state.items.filter(item => item.product.id !== action.payload.productId);
      
      return {
        ...state,
        items: updatedItems,
        totalItems: state.totalItems - itemToRemove.quantity,
        totalPrice: state.totalPrice - itemToRemove.total_price,
      };
    }
    
    case 'UPDATE_QUANTITY': {
      const { productId, quantity } = action.payload;
      const existingItem = state.items.find(item => item.product.id === productId);
      
      if (!existingItem) return state;
      
      if (quantity <= 0) {
        return cartReducer(state, { type: 'REMOVE_ITEM', payload: { productId } });
      }
      
      const updatedItems = state.items.map(item =>
        item.product.id === productId
          ? {
              ...item,
              quantity,
              total_price: quantity * item.unit_price,
            }
          : item
      );
      
      const totalItems = updatedItems.reduce((sum, item) => sum + item.quantity, 0);
      const totalPrice = updatedItems.reduce((sum, item) => sum + item.total_price, 0);
      
      return {
        ...state,
        items: updatedItems,
        totalItems,
        totalPrice,
      };
    }
    
    case 'CLEAR_CART':
      return {
        items: [],
        totalItems: 0,
        totalPrice: 0,
      };
    
    default:
      return state;
  }
};

const initialState: CartState = {
  items: [],
  totalItems: 0,
  totalPrice: 0,
};

export const CartProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(cartReducer, initialState);

  const addItem = (product: Product, quantity: number) => {
    dispatch({ type: 'ADD_ITEM', payload: { product, quantity } });
  };

  const removeItem = (productId: number) => {
    dispatch({ type: 'REMOVE_ITEM', payload: { productId } });
  };

  const updateQuantity = (productId: number, quantity: number) => {
    dispatch({ type: 'UPDATE_QUANTITY', payload: { productId, quantity } });
  };

  const clearCart = () => {
    dispatch({ type: 'CLEAR_CART' });
  };

  const getItemQuantity = (productId: number): number => {
    const item = state.items.find(item => item.product.id === productId);
    return item ? item.quantity : 0;
  };

  const value: CartContextType = {
    state,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    getItemQuantity,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

export const useCart = (): CartContextType => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};