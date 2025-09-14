import React from 'react';

interface StatusBadgeProps {
  status: 'available' | 'free' | 'occupied' | 'offline' | 'category_view';
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'available':
      case 'free':  // Handle 'free' status from API
        return {
          bg: 'bg-green-50',
          text: 'text-green-700',
          border: 'border-green-200',
          label: 'Available',
          icon: '●'
        };
      case 'occupied':
        return {
          bg: 'bg-red-50',
          text: 'text-red-700',
          border: 'border-red-200',
          label: 'In Use',
          icon: '●'
        };
      case 'offline':
        return {
          bg: 'bg-gray-50',
          text: 'text-gray-700',
          border: 'border-gray-200',
          label: 'Offline',
          icon: '●'
        };
      case 'category_view':
        return {
          bg: 'bg-blue-50',
          text: 'text-blue-700',
          border: 'border-blue-200',
          label: 'Category View',
          icon: '📊'
        };
      default:
        return {
          bg: 'bg-gray-50',
          text: 'text-gray-700',
          border: 'border-gray-200',
          label: 'Unknown',
          icon: '●'
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium border ${config.bg} ${config.text} ${config.border}`}>
      <span className="text-xs">{config.icon}</span>
      {config.label}
    </div>
  );
}