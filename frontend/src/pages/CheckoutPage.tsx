import React, { useState, useEffect } from 'react';
import { useCart } from '../contexts/CartContext';
import { ShippingAddress, BillingAddress, OrderCalculation } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Header } from '../components/Header';
import { ArrowLeft, CreditCard, Truck, CheckCircle } from 'lucide-react';
import { ordersApi } from '../services/api';

export const CheckoutPage: React.FC = () => {
  const { state, clearCart } = useCart();
  const { items, totalPrice } = state;
  
  const [currentStep, setCurrentStep] = useState(1);
  const [shippingAddress, setShippingAddress] = useState<ShippingAddress>({
    first_name: '',
    last_name: '',
    company: '',
    street_address: '',
    apartment: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'US',
    phone: '',
  });
  
  const [billingAddress, setBillingAddress] = useState<BillingAddress>({
    first_name: '',
    last_name: '',
    company: '',
    street_address: '',
    apartment: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'US',
    phone: '',
  });
  
  const [useSameAddress, setUseSameAddress] = useState(true);
  const [paymentMethod, setPaymentMethod] = useState<'credit_card' | 'paypal'>('credit_card');
  const [orderNotes, setOrderNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [orderCalculation, setOrderCalculation] = useState<OrderCalculation>({
    subtotal: 0,
    tax_amount: 0,
    shipping_cost: 0,
    total_amount: 0,
    currency: 'USD',
  });

  // Calculate order totals
  useEffect(() => {
    const calculateTotals = async () => {
      try {
        const checkoutData = {
          shipping_address: shippingAddress,
          billing_address: useSameAddress ? shippingAddress : billingAddress,
          payment_method: paymentMethod,
          notes: orderNotes,
        };
        
        const response = await ordersApi.calculateOrder(checkoutData);
        setOrderCalculation(response.data);
      } catch (error) {
        console.error('Error calculating order totals:', error);
        // Fallback to client-side calculation
        const subtotal = totalPrice;
        const taxRate = 0.08;
        const taxAmount = subtotal * taxRate;
        const shippingCost = subtotal > 100 ? 0 : 15;
        const totalAmount = subtotal + taxAmount + shippingCost;

        setOrderCalculation({
          subtotal,
          tax_amount: taxAmount,
          shipping_cost: shippingCost,
          total_amount: totalAmount,
          currency: 'USD',
        });
      }
    };

    if (items.length > 0) {
      calculateTotals();
    }
  }, [totalPrice, shippingAddress, billingAddress, useSameAddress, paymentMethod, orderNotes, items.length]);

  // Redirect if cart is empty
  useEffect(() => {
    if (items.length === 0) {
      // Redirect to product catalog
      window.location.href = '/';
    }
  }, [items.length]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const handleShippingChange = (field: keyof ShippingAddress, value: string) => {
    setShippingAddress(prev => ({ ...prev, [field]: value }));
  };

  const handleBillingChange = (field: keyof BillingAddress, value: string) => {
    setBillingAddress(prev => ({ ...prev, [field]: value }));
  };

  const handleUseSameAddressChange = (checked: boolean) => {
    setUseSameAddress(checked);
    if (checked) {
      setBillingAddress(shippingAddress);
    }
  };

  const handleNextStep = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePreviousStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handlePlaceOrder = async () => {
    setIsProcessing(true);
    
    try {
      const checkoutData = {
        shipping_address: shippingAddress,
        billing_address: useSameAddress ? shippingAddress : billingAddress,
        payment_method: paymentMethod,
        notes: orderNotes,
      };
      
      const response = await ordersApi.createOrder(checkoutData);
      console.log('Order created:', response.data);
      
      // Clear cart and show success
      clearCart();
      setCurrentStep(4);
    } catch (error) {
      console.error('Error placing order:', error);
      // TODO: Show error message to user
      alert('Failed to place order. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const isShippingValid = () => {
    return shippingAddress.first_name && 
           shippingAddress.last_name && 
           shippingAddress.street_address && 
           shippingAddress.city && 
           shippingAddress.state && 
           shippingAddress.postal_code;
  };

  const isBillingValid = () => {
    if (useSameAddress) return true;
    return billingAddress.first_name && 
           billingAddress.last_name && 
           billingAddress.street_address && 
           billingAddress.city && 
           billingAddress.state && 
           billingAddress.postal_code;
  };

  if (items.length === 0) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        onSearch={() => {}}
        user={null}
        onLogin={() => console.log('Login clicked')}
        onLogout={() => console.log('Logout clicked')}
      />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => window.history.back()}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Shopping
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">Checkout</h1>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-8">
            {[
              { step: 1, title: 'Shipping', icon: Truck },
              { step: 2, title: 'Payment', icon: CreditCard },
              { step: 3, title: 'Review', icon: CheckCircle },
            ].map(({ step, title, icon: Icon }) => (
              <div key={step} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  currentStep >= step 
                    ? 'bg-primary border-primary text-primary-foreground' 
                    : 'border-gray-300 text-gray-500'
                }`}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className={`ml-2 text-sm font-medium ${
                  currentStep >= step ? 'text-primary' : 'text-gray-500'
                }`}>
                  {title}
                </span>
                {step < 3 && (
                  <div className={`w-8 h-0.5 ml-4 ${
                    currentStep > step ? 'bg-primary' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Step 1: Shipping Information */}
            {currentStep === 1 && (
              <Card>
                <CardHeader>
                  <CardTitle>Shipping Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      placeholder="First Name"
                      value={shippingAddress.first_name}
                      onChange={(e) => handleShippingChange('first_name', e.target.value)}
                    />
                    <Input
                      placeholder="Last Name"
                      value={shippingAddress.last_name}
                      onChange={(e) => handleShippingChange('last_name', e.target.value)}
                    />
                  </div>
                  
                  <Input
                    placeholder="Company (Optional)"
                    value={shippingAddress.company}
                    onChange={(e) => handleShippingChange('company', e.target.value)}
                  />
                  
                  <Input
                    placeholder="Street Address"
                    value={shippingAddress.street_address}
                    onChange={(e) => handleShippingChange('street_address', e.target.value)}
                  />
                  
                  <Input
                    placeholder="Apartment, suite, etc. (Optional)"
                    value={shippingAddress.apartment}
                    onChange={(e) => handleShippingChange('apartment', e.target.value)}
                  />
                  
                  <div className="grid grid-cols-3 gap-4">
                    <Input
                      placeholder="City"
                      value={shippingAddress.city}
                      onChange={(e) => handleShippingChange('city', e.target.value)}
                    />
                    <Input
                      placeholder="State"
                      value={shippingAddress.state}
                      onChange={(e) => handleShippingChange('state', e.target.value)}
                    />
                    <Input
                      placeholder="ZIP Code"
                      value={shippingAddress.postal_code}
                      onChange={(e) => handleShippingChange('postal_code', e.target.value)}
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <select
                      className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                      value={shippingAddress.country}
                      onChange={(e) => handleShippingChange('country', e.target.value)}
                    >
                      <option value="US">United States</option>
                      <option value="CA">Canada</option>
                    </select>
                    <Input
                      placeholder="Phone Number"
                      value={shippingAddress.phone}
                      onChange={(e) => handleShippingChange('phone', e.target.value)}
                    />
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Step 2: Payment Information */}
            {currentStep === 2 && (
              <Card>
                <CardHeader>
                  <CardTitle>Payment Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Billing Address */}
                  <div>
                    <div className="flex items-center space-x-2 mb-4">
                      <input
                        type="checkbox"
                        id="use-same-address"
                        checked={useSameAddress}
                        onChange={(e) => handleUseSameAddressChange(e.target.checked)}
                        className="rounded border-gray-300"
                      />
                      <label htmlFor="use-same-address" className="text-sm font-medium">
                        Use same address for billing
                      </label>
                    </div>
                    
                    {!useSameAddress && (
                      <div className="space-y-4">
                        <h4 className="font-semibold">Billing Address</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <Input
                            placeholder="First Name"
                            value={billingAddress.first_name}
                            onChange={(e) => handleBillingChange('first_name', e.target.value)}
                          />
                          <Input
                            placeholder="Last Name"
                            value={billingAddress.last_name}
                            onChange={(e) => handleBillingChange('last_name', e.target.value)}
                          />
                        </div>
                        
                        <Input
                          placeholder="Street Address"
                          value={billingAddress.street_address}
                          onChange={(e) => handleBillingChange('street_address', e.target.value)}
                        />
                        
                        <div className="grid grid-cols-3 gap-4">
                          <Input
                            placeholder="City"
                            value={billingAddress.city}
                            onChange={(e) => handleBillingChange('city', e.target.value)}
                          />
                          <Input
                            placeholder="State"
                            value={billingAddress.state}
                            onChange={(e) => handleBillingChange('state', e.target.value)}
                          />
                          <Input
                            placeholder="ZIP Code"
                            value={billingAddress.postal_code}
                            onChange={(e) => handleBillingChange('postal_code', e.target.value)}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Payment Method */}
                  <div>
                    <h4 className="font-semibold mb-4">Payment Method</h4>
                    <div className="space-y-3">
                      <label className="flex items-center space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                        <input
                          type="radio"
                          name="payment"
                          value="credit_card"
                          checked={paymentMethod === 'credit_card'}
                          onChange={(e) => setPaymentMethod(e.target.value as 'credit_card')}
                          className="text-primary"
                        />
                        <CreditCard className="w-5 h-5" />
                        <span>Credit Card</span>
                      </label>
                      
                      <label className="flex items-center space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                        <input
                          type="radio"
                          name="payment"
                          value="paypal"
                          checked={paymentMethod === 'paypal'}
                          onChange={(e) => setPaymentMethod(e.target.value as 'paypal')}
                          className="text-primary"
                        />
                        <div className="w-5 h-5 bg-blue-600 rounded flex items-center justify-center">
                          <span className="text-white text-xs font-bold">P</span>
                        </div>
                        <span>PayPal</span>
                      </label>
                    </div>
                  </div>

                  {/* Order Notes */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Order Notes (Optional)</label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                      rows={3}
                      placeholder="Special instructions for your order..."
                      value={orderNotes}
                      onChange={(e) => setOrderNotes(e.target.value)}
                    />
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Step 3: Review Order */}
            {currentStep === 3 && (
              <Card>
                <CardHeader>
                  <CardTitle>Review Your Order</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-semibold mb-2">Shipping Address</h4>
                      <p className="text-gray-600">
                        {shippingAddress.first_name} {shippingAddress.last_name}<br />
                        {shippingAddress.street_address}<br />
                        {shippingAddress.apartment && `${shippingAddress.apartment}, `}
                        {shippingAddress.city}, {shippingAddress.state} {shippingAddress.postal_code}<br />
                        {shippingAddress.country}
                      </p>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-2">Payment Method</h4>
                      <p className="text-gray-600 capitalize">
                        {paymentMethod.replace('_', ' ')}
                      </p>
                    </div>
                    
                    {orderNotes && (
                      <div>
                        <h4 className="font-semibold mb-2">Order Notes</h4>
                        <p className="text-gray-600">{orderNotes}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Step 4: Order Confirmation */}
            {currentStep === 4 && (
              <Card>
                <CardContent className="text-center py-12">
                  <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">Order Placed Successfully!</h2>
                  <p className="text-gray-600 mb-6">
                    Thank you for your order. You will receive a confirmation email shortly.
                  </p>
                  <Button onClick={() => window.location.href = '/'}>
                    Continue Shopping
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Navigation Buttons */}
            {currentStep < 4 && (
              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={handlePreviousStep}
                  disabled={currentStep === 1}
                >
                  Previous
                </Button>
                
                {currentStep < 3 ? (
                  <Button
                    onClick={handleNextStep}
                    disabled={
                      (currentStep === 1 && !isShippingValid()) ||
                      (currentStep === 2 && !isBillingValid())
                    }
                  >
                    Next
                  </Button>
                ) : (
                  <Button
                    onClick={handlePlaceOrder}
                    disabled={isProcessing}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {isProcessing ? 'Processing...' : 'Place Order'}
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Order Summary Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Cart Items */}
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {items.map((item) => (
                      <div key={item.id} className="flex items-center space-x-3 text-sm">
                        <img
                          src={item.product.images?.[0]?.image_url || '/placeholder-product.jpg'}
                          alt={item.product.name}
                          className="w-12 h-12 rounded object-cover"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{item.product.name}</p>
                          <p className="text-gray-500">Qty: {item.quantity}</p>
                        </div>
                        <p className="font-medium">{formatPrice(item.total_price)}</p>
                      </div>
                    ))}
                  </div>
                  
                  {/* Order Totals */}
                  <div className="border-t pt-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Subtotal</span>
                      <span>{formatPrice(orderCalculation.subtotal)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Tax</span>
                      <span>{formatPrice(orderCalculation.tax_amount)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Shipping</span>
                      <span>
                        {orderCalculation.shipping_cost === 0 ? 'Free' : formatPrice(orderCalculation.shipping_cost)}
                      </span>
                    </div>
                    <div className="flex justify-between font-semibold text-lg border-t pt-2">
                      <span>Total</span>
                      <span>{formatPrice(orderCalculation.total_amount)}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
