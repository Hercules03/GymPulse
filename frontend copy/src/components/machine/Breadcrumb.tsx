import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { createPageUrl } from '@/utils';

interface BreadcrumbProps {
  machineName: string;
  category: string;
}

export default function Breadcrumb({ machineName, category }: BreadcrumbProps) {
  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-500 mb-6">
      <Link 
        to={createPageUrl('Dashboard')} 
        className="flex items-center hover:text-gray-700 transition-colors"
      >
        <Home className="w-4 h-4" />
      </Link>
      <ChevronRight className="w-4 h-4" />
      <span className="capitalize">{category}</span>
      <ChevronRight className="w-4 h-4" />
      <span className="text-gray-900 font-medium">{machineName}</span>
    </nav>
  );
}