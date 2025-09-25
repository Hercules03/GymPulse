import React from 'react';

interface StatusBadgeProps {
  status: 'available' | 'free' | 'occupied' | 'offline' | 'unknown' | 'category_view';
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  console.log('StatusBadge received status:', status, typeof status);
  
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'available':
      case 'free':  // Handle 'free' status from API
        return {
          dotColor: 'bg-green-500',
          label: 'Available'
        };
      case 'occupied':
        return {
          dotColor: 'bg-red-500',
          label: 'In Use'
        };
      case 'offline':
        return {
          dotColor: 'bg-gray-400',
          label: 'Offline'
        };
      case 'category_view':
        return {
          dotColor: 'bg-blue-500',
          label: 'Category View'
        };
      default:
        return {
          dotColor: 'bg-gray-400',
          label: 'Unknown'
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <div className={`w-3 h-3 rounded-full ${config.dotColor}`} title={config.label}></div>
  );
}