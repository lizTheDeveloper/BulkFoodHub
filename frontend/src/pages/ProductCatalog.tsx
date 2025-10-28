import React, { useState, useEffect } from 'react';
import { Product, ProductSearchParams, Category, ProductListResponse } from '../types';
import { ProductGrid } from '../components/ProductGrid';
import { SearchAndFilter } from '../components/SearchAndFilter';
import { Header } from '../components/Header';
import { ProductDetail } from '../components/ProductDetail';
import api from '../services/api';

export const ProductCatalog: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useState<ProductSearchParams>({
    page: 1,
    size: 20,
    offset: 0,
    sort_by: 'created_at',
    sort_order: 'desc',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    size: 20,
    total: 0,
  });
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Fetch products
  const fetchProducts = async (params: ProductSearchParams) => {
    try {
      setLoading(true);
      const response = await api.get<ProductListResponse>('/api/v1/products/', {
        params: {
          page: params.page || 1,
          size: params.size || 20,
          ...params,
        },
      });
      
      setProducts(response.data.products);
      setPagination({
        page: response.data.page,
        size: response.data.size,
        total: response.data.total,
      });
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch categories
  const fetchCategories = async () => {
    try {
      const response = await api.get<Category[]>('/api/v1/products/categories/');
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  // Initial load
  useEffect(() => {
    fetchProducts(searchParams);
    fetchCategories();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle search parameter changes
  const handleSearchChange = (newParams: ProductSearchParams) => {
    const updatedParams = { ...newParams, page: 1, offset: 0 };
    setSearchParams(updatedParams);
    fetchProducts(updatedParams);
  };

  // Handle search from header
  const handleHeaderSearch = (query: string) => {
    const newParams = { ...searchParams, query, page: 1, offset: 0 };
    setSearchParams(newParams);
    fetchProducts(newParams);
  };

  // Handle pagination
  const handlePageChange = (newPage: number) => {
    const newParams = {
      ...searchParams,
      page: newPage,
      offset: (newPage - 1) * (searchParams.size || 20),
    };
    setSearchParams(newParams);
    fetchProducts(newParams);
  };

  // Handle product actions
  const handleViewDetails = (product: Product) => {
    setSelectedProduct(product);
  };

  const handleCheckout = () => {
    if ((window as any).navigateTo) {
      (window as any).navigateTo('checkout');
    }
  };

  const handleBackToList = () => {
    setSelectedProduct(null);
  };

  const totalPages = Math.ceil(pagination.total / pagination.size);

  // Show product detail if a product is selected
  if (selectedProduct) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header
          onSearch={handleHeaderSearch}
          user={null}
          onLogin={() => console.log('Login clicked')}
          onLogout={() => console.log('Logout clicked')}
          onCheckout={handleCheckout}
        />
        <ProductDetail
          product={selectedProduct}
          onBack={handleBackToList}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        onSearch={handleHeaderSearch}
        user={null}
        onLogin={() => console.log('Login clicked')}
        onLogout={() => console.log('Logout clicked')}
        onCheckout={handleCheckout}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Browse Products
          </h1>
          <p className="text-gray-600">
            Discover high-quality bulk food products from trusted suppliers
          </p>
        </div>

        <div className="space-y-6">
          <SearchAndFilter
            searchParams={searchParams}
            onSearchChange={handleSearchChange}
            categories={categories}
            loading={loading}
          />

          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {products.length} of {pagination.total} products
            </div>
            <div className="text-sm text-gray-500">
              Page {pagination.page} of {totalPages}
            </div>
          </div>

          <ProductGrid
            products={products}
            onViewDetails={handleViewDetails}
            loading={loading}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center space-x-2">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page === 1}
                className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const page = i + 1;
                return (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`px-3 py-2 text-sm font-medium rounded-md ${
                      page === pagination.page
                        ? 'bg-primary text-primary-foreground'
                        : 'text-gray-500 bg-white border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                );
              })}
              
              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page === totalPages}
                className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
