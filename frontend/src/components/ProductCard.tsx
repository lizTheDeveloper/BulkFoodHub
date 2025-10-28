import React, { useState } from 'react';
import { Product } from '../types';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { ShoppingCart, Eye, Plus, Minus } from 'lucide-react';
import { useCart } from '../contexts/CartContext';

interface ProductCardProps {
  product: Product;
  onViewDetails: (product: Product) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  product,
  onViewDetails,
}) => {
  const { addItem, getItemQuantity } = useCart();
  const [quantity, setQuantity] = useState(1);
  const cartQuantity = getItemQuantity(product.id);
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const getAvailabilityBadge = () => {
    if (!product.is_active) {
      return <Badge variant="destructive">Inactive</Badge>;
    }
    if (!product.is_approved) {
      return <Badge variant="secondary">Pending Approval</Badge>;
    }
    if (product.available_quantity === 0) {
      return <Badge variant="destructive">Out of Stock</Badge>;
    }
    if (product.available_quantity < 10) {
      return <Badge variant="secondary">Low Stock</Badge>;
    }
    return <Badge variant="default">In Stock</Badge>;
  };

  const getPrimaryImage = () => {
    if (product.images && product.images.length > 0) {
      const primaryImage = product.images.find(img => img.is_primary);
      return primaryImage?.image_url || product.images[0].image_url;
    }
    return '/placeholder-product.svg';
  };

  const handleAddToCart = () => {
    addItem(product, quantity);
    setQuantity(1); // Reset quantity after adding
  };

  const handleQuantityChange = (newQuantity: number) => {
    if (newQuantity >= 1 && newQuantity <= product.available_quantity) {
      setQuantity(newQuantity);
    }
  };

  return (
    <Card className="h-full flex flex-col hover:shadow-lg transition-shadow">
      <CardHeader className="pb-2">
        <div className="aspect-square w-full bg-gray-100 rounded-md mb-2 overflow-hidden">
          <img
            src={getPrimaryImage()}
            alt={product.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/placeholder-product.svg';
            }}
          />
        </div>
        <CardTitle className="text-lg line-clamp-2">{product.name}</CardTitle>
        {product.supplier_business_name && (
          <p className="text-sm text-muted-foreground">
            by {product.supplier_business_name}
          </p>
        )}
      </CardHeader>
      
      <CardContent className="flex-1 pb-2">
        <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
          {product.description}
        </p>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-primary">
              {formatPrice(product.price_per_unit)}
            </span>
            <span className="text-sm text-muted-foreground">
              per {product.unit}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-sm">
              Available: {product.available_quantity} {product.unit}s
            </span>
            {getAvailabilityBadge()}
          </div>
          
          {product.category && (
            <Badge variant="outline" className="text-xs">
              {product.category.replace('_', ' ').toUpperCase()}
            </Badge>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="pt-2">
        <div className="w-full space-y-2">
          {/* Quantity Selector */}
          <div className="flex items-center justify-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuantityChange(quantity - 1)}
              disabled={quantity <= 1}
              className="h-8 w-8 p-0"
            >
              <Minus className="h-4 w-4" />
            </Button>
            <span className="text-sm font-medium w-8 text-center">
              {quantity}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleQuantityChange(quantity + 1)}
              disabled={quantity >= product.available_quantity}
              className="h-8 w-8 p-0"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          
          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => onViewDetails(product)}
            >
              <Eye className="w-4 h-4 mr-2" />
              View
            </Button>
            <Button
              size="sm"
              className="flex-1"
              onClick={handleAddToCart}
              disabled={!product.is_active || !product.is_approved || product.available_quantity === 0}
            >
              <ShoppingCart className="w-4 h-4 mr-2" />
              Add to Cart
            </Button>
          </div>
          
          {/* Cart Status */}
          {cartQuantity > 0 && (
            <p className="text-xs text-center text-green-600">
              {cartQuantity} in cart
            </p>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};
