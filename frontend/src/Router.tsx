import React, { useState, useEffect } from 'react';
import { ProductCatalog } from './pages/ProductCatalog';
import { CheckoutPage } from './pages/CheckoutPage';

type Route = 'catalog' | 'checkout';

export const Router: React.FC = () => {
  const [currentRoute, setCurrentRoute] = useState<Route>('catalog');

  // Handle browser navigation
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      if (path === '/checkout') {
        setCurrentRoute('checkout');
      } else {
        setCurrentRoute('catalog');
      }
    };

    // Set initial route based on URL
    handlePopState();

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateTo = (route: Route) => {
    setCurrentRoute(route);
    const path = route === 'checkout' ? '/checkout' : '/';
    window.history.pushState({}, '', path);
  };

  // Expose navigation function globally for components to use
  useEffect(() => {
    (window as any).navigateTo = navigateTo;
  }, []);

  switch (currentRoute) {
    case 'checkout':
      return <CheckoutPage />;
    case 'catalog':
    default:
      return <ProductCatalog />;
  }
};
