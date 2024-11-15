import React from 'react';
import { formatPrice } from '../utils/formatPrice';

interface PriceDisplayProps {
  price: number;
}

const PriceDisplay: React.FC<PriceDisplayProps> = ({ price }) => {
  return <span>{formatPrice(price)}</span>;
};

export default PriceDisplay;