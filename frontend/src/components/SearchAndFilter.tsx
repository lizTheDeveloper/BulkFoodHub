import React, { useState } from 'react';
import { Search, Filter, X } from 'lucide-react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { Badge } from './ui/Badge';
import { ProductSearchParams, Category } from '../types';

interface SearchAndFilterProps {
  searchParams: ProductSearchParams;
  onSearchChange: (params: ProductSearchParams) => void;
  categories: Category[];
  loading?: boolean;
}

export const SearchAndFilter: React.FC<SearchAndFilterProps> = ({
  searchParams,
  onSearchChange,
  categories,
  loading = false,
}) => {
  const [showFilters, setShowFilters] = useState(false);
  const [localParams, setLocalParams] = useState<ProductSearchParams>(searchParams);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearchChange(localParams);
  };

  const handleInputChange = (field: keyof ProductSearchParams, value: any) => {
    const newParams = { ...localParams, [field]: value };
    setLocalParams(newParams);
  };

  const handleCategorySelect = (category: string) => {
    const newParams = {
      ...localParams,
      category: localParams.category === category ? undefined : category,
    };
    setLocalParams(newParams);
    onSearchChange(newParams);
  };

  const clearFilters = () => {
    const clearedParams: ProductSearchParams = {
      query: '',
      category: undefined,
      supplier_id: undefined,
      min_price: undefined,
      max_price: undefined,
      min_quantity: undefined,
      is_active: undefined,
      is_approved: undefined,
      sort_by: 'created_at',
      sort_order: 'desc',
    };
    setLocalParams(clearedParams);
    onSearchChange(clearedParams);
  };

  const activeFiltersCount = Object.values(localParams).filter(
    (value) => value !== undefined && value !== '' && value !== 'created_at' && value !== 'desc'
  ).length;

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            type="text"
            placeholder="Search products..."
            value={localParams.query || ''}
            onChange={(e) => handleInputChange('query', e.target.value)}
            className="pl-10"
          />
        </div>
        <Button type="submit" disabled={loading}>
          Search
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter className="w-4 h-4 mr-2" />
          Filters
          {activeFiltersCount > 0 && (
            <Badge variant="secondary" className="ml-2">
              {activeFiltersCount}
            </Badge>
          )}
        </Button>
      </form>

      {/* Categories */}
      <div className="flex flex-wrap gap-2">
        {categories.map((category) => (
          <Button
            key={category.value}
            variant={localParams.category === category.value ? "default" : "outline"}
            size="sm"
            onClick={() => handleCategorySelect(category.value)}
          >
            {category.name} ({category.product_count})
          </Button>
        ))}
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Advanced Filters</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFilters(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Min Price</label>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={localParams.min_price || ''}
                  onChange={(e) => handleInputChange('min_price', e.target.value ? parseFloat(e.target.value) : undefined)}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Max Price</label>
                <Input
                  type="number"
                  placeholder="1000.00"
                  value={localParams.max_price || ''}
                  onChange={(e) => handleInputChange('max_price', e.target.value ? parseFloat(e.target.value) : undefined)}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Min Quantity</label>
                <Input
                  type="number"
                  placeholder="1"
                  value={localParams.min_quantity || ''}
                  onChange={(e) => handleInputChange('min_quantity', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Sort By</label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  value={localParams.sort_by || 'created_at'}
                  onChange={(e) => handleInputChange('sort_by', e.target.value)}
                >
                  <option value="created_at">Date Added</option>
                  <option value="name">Name</option>
                  <option value="price_per_unit">Price</option>
                  <option value="available_quantity">Quantity</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button onClick={handleSearch} disabled={loading}>
                Apply Filters
              </Button>
              <Button variant="outline" onClick={clearFilters}>
                Clear All
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
