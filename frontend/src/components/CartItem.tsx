import React from 'react';
import { Minus, Plus, Trash2, X } from 'lucide-react';
import { useCart } from '../contexts/CartContext';
import { CartItem as CartItemType } from '../types';
import { Button } from './ui/Button';
import { cn } from '../lib/utils';

interface CartItemProps {
  item: CartItemType;
  onRemove?: (itemId: string) => void;
  onUpdateQuantity?: (itemId: string, quantity: number) => void;
  showRemoveButton?: boolean;
  className?: string;
}

export const CartItem: React.FC<CartItemProps> = ({
  item,
  onRemove,
  onUpdateQuantity,
  showRemoveButton = true,
  className,
}) => {
  const { updateQuantity, removeItem } = useCart();

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity < 0) return;
    if (newQuantity > item.product.available_quantity) {
      // Show error or handle max quantity reached
      return;
    }
    
    if (onUpdateQuantity) {
      onUpdateQuantity(item.id, newQuantity);
    } else {
      updateQuantity(item.id, newQuantity);
    }
  };

  const handleRemove = () => {
    if (onRemove) {
      onRemove(item.id);
    } else {
      removeItem(item.id);
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  return (
    <div className={cn('flex items-center space-x-4 p-4 border-b border-gray-200', className)}>
      {/* Product Image */}
      <div className="flex-shrink-0">
        <img
          src={item.product.images?.[0]?.image_url || '/placeholder-product.jpg'}
          alt={item.product.name}
          className="h-16 w-16 rounded-lg object-cover"
        />
      </div>

      {/* Product Details */}
      <div className="flex-1 min-w-0">
        <h3 className="text-sm font-medium text-gray-900 truncate">
          {item.product.name}
        </h3>
        <p className="text-sm text-gray-500">
          {item.product.supplier_name || 'Unknown Supplier'}
        </p>
        <p className="text-sm text-gray-500">
          {formatPrice(item.unit_price)} per {item.product.unit}
        </p>
        {item.product.available_quantity < item.quantity && (
          <p className="text-xs text-red-600 mt-1">
            Only {item.product.available_quantity} available
          </p>
        )}
      </div>

      {/* Quantity Controls */}
      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleQuantityChange(item.quantity - 1)}
          disabled={item.quantity <= 1}
          className="h-8 w-8 p-0"
        >
          <Minus className="h-4 w-4" />
        </Button>
        
        <span className="text-sm font-medium w-8 text-center">
          {item.quantity}
        </span>
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleQuantityChange(item.quantity + 1)}
          disabled={item.quantity >= item.product.available_quantity}
          className="h-8 w-8 p-0"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Price */}
      <div className="text-right">
        <p className="text-sm font-medium text-gray-900">
          {formatPrice(item.total_price)}
        </p>
      </div>

      {/* Remove Button */}
      {showRemoveButton && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRemove}
          className="h-8 w-8 p-0 text-gray-400 hover:text-red-600"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
};
