import React, { useState } from 'react';
import { User, Search } from 'lucide-react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { CartIcon } from './CartIcon';
import { CartDrawer } from './CartDrawer';
import { useCart } from '../contexts/CartContext';

interface HeaderProps {
  onSearch: (query: string) => void;
  user?: any;
  onLogin?: () => void;
  onLogout?: () => void;
  onCheckout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onSearch,
  user,
  onLogin,
  onLogout,
  onCheckout,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isCartOpen, setIsCartOpen] = useState(false);
  const { state } = useCart();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-primary">
              BulkFoodHub
            </h1>
          </div>

          {/* Search Bar */}
          <div className="flex-1 max-w-lg mx-8">
            <form onSubmit={handleSearch} className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-full"
              />
            </form>
          </div>

          {/* Navigation */}
          <div className="flex items-center space-x-4">
            {/* Cart */}
            <CartIcon onClick={() => setIsCartOpen(true)} />

            {/* User Menu */}
            {user ? (
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="icon">
                  <User className="w-5 h-5" />
                </Button>
                <span className="text-sm text-gray-700">
                  {user.first_name} {user.last_name}
                </span>
                <Button variant="outline" size="sm" onClick={onLogout}>
                  Logout
                </Button>
              </div>
            ) : (
              <Button onClick={onLogin}>
                Login
              </Button>
            )}
          </div>
        </div>
      </div>
      
      {/* Cart Drawer */}
      <CartDrawer
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        onCheckout={onCheckout}
      />
    </header>
  );
};
