import React from 'react';
import { ShoppingCart } from 'lucide-react';
import { Button } from './ui/Button';
import { useCart } from '../contexts/CartContext';

interface CartIconProps {
  onClick: () => void;
}

export const CartIcon: React.FC<CartIconProps> = ({ onClick }) => {
  const { state } = useCart();

  return (
    <Button variant="ghost" size="icon" className="relative" onClick={onClick}>
      <ShoppingCart className="w-5 h-5" />
      {state.totalItems > 0 && (
        <span className="absolute -top-1 -right-1 bg-primary text-primary-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center">
          {state.totalItems}
        </span>
      )}
    </Button>
  );
};