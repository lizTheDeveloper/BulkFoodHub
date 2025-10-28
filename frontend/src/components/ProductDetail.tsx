import React, { useState } from 'react';
import { Product } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { ShoppingCart, Heart, Share2, ArrowLeft } from 'lucide-react';
import { useCart } from '../contexts/CartContext';

interface ProductDetailProps {
  product: Product;
  onBack: () => void;
}

export const ProductDetail: React.FC<ProductDetailProps> = ({
  product,
  onBack,
}) => {
  const { addItem, getItemQuantity } = useCart();
  const [quantity, setQuantity] = useState(1);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
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

  const getImages = () => {
    if (product.images && product.images.length > 0) {
      return product.images;
    }
    return [{ id: 0, product_id: product.id, image_url: '/placeholder-product.svg', is_primary: true }];
  };

  const images = getImages();
  const maxQuantity = Math.min(product.available_quantity, 100);

  const handleAddToCart = () => {
    addItem(product, quantity);
    setQuantity(1); // Reset quantity after adding
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Button
        variant="ghost"
        onClick={onBack}
        className="mb-6"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Products
      </Button>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Product Images */}
        <div className="space-y-4">
          <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={images[selectedImageIndex]?.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder-product.svg';
              }}
            />
          </div>
          
          {images.length > 1 && (
            <div className="grid grid-cols-4 gap-2">
              {images.map((image, index) => (
                <button
                  key={image.id}
                  onClick={() => setSelectedImageIndex(index)}
                  className={`aspect-square bg-gray-100 rounded-md overflow-hidden border-2 ${
                    index === selectedImageIndex ? 'border-primary' : 'border-transparent'
                  }`}
                >
                  <img
                    src={image.image_url}
                    alt={`${product.name} ${index + 1}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/placeholder-product.svg';
                    }}
                  />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>
              {getAvailabilityBadge()}
            </div>
            
            {product.supplier_business_name && (
              <p className="text-lg text-gray-600 mb-4">
                by {product.supplier_business_name}
              </p>
            )}

            <div className="flex items-center gap-4 mb-6">
              <span className="text-4xl font-bold text-primary">
                {formatPrice(product.price_per_unit)}
              </span>
              <span className="text-lg text-gray-500">
                per {product.unit}
              </span>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Product Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Description</h4>
                <p className="text-gray-600">{product.description}</p>
              </div>

              {product.ingredients && (
                <div>
                  <h4 className="font-semibold mb-2">Ingredients</h4>
                  <p className="text-gray-600">{product.ingredients}</p>
                </div>
              )}

              {product.nutritional_info && (
                <div>
                  <h4 className="font-semibold mb-2">Nutritional Information</h4>
                  <p className="text-gray-600">{product.nutritional_info}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold mb-1">Category</h4>
                  <Badge variant="outline">
                    {product.category?.replace('_', ' ').toUpperCase()}
                  </Badge>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Available Quantity</h4>
                  <p className="text-gray-600">
                    {product.available_quantity} {product.unit}s
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Add to Cart */}
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <label className="font-semibold">Quantity:</label>
                  <Input
                    type="number"
                    min="1"
                    max={maxQuantity}
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, Math.min(maxQuantity, parseInt(e.target.value) || 1)))}
                    className="w-20"
                  />
                  <span className="text-sm text-gray-500">
                    Max: {maxQuantity}
                  </span>
                </div>

                <div className="flex gap-2">
                  <Button
                    size="lg"
                    className="flex-1"
                    onClick={handleAddToCart}
                    disabled={!product.is_active || !product.is_approved || product.available_quantity === 0}
                  >
                    <ShoppingCart className="w-5 h-5 mr-2" />
                    Add to Cart - {formatPrice(product.price_per_unit * quantity)}
                  </Button>
                  
                  <Button variant="outline" size="lg">
                    <Heart className="w-5 h-5" />
                  </Button>
                  
                  <Button variant="outline" size="lg">
                    <Share2 className="w-5 h-5" />
                  </Button>
                </div>
                
                {/* Cart Status */}
                {cartQuantity > 0 && (
                  <div className="text-center">
                    <p className="text-sm text-green-600 font-medium">
                      {cartQuantity} {cartQuantity === 1 ? 'item' : 'items'} in cart
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
