import React from 'react';
import { Card, CardContent } from "@/components/ui/card";

interface Machine {
  name: string;
  status: 'available' | 'occupied' | 'offline';
  machine_id: string;
}

interface CategoryCardProps {
  category: string;
  totalMachines: number;
  availableCount: number;
  occupiedCount: number;
  offlineCount: number;
  machines: Machine[];
}

export default function CategoryCard({ 
  category, 
  totalMachines, 
  availableCount, 
  occupiedCount, 
  offlineCount 
}: CategoryCardProps) {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'legs':
        return '🦵';
      case 'chest':
        return '💪';
      case 'back':
        return '🔙';
      default:
        return '🏋️';
    }
  };

  const availabilityPercentage = totalMachines > 0 ? (availableCount / totalMachines) * 100 : 0;

  return (
    <Card className="border-0 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer h-full">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center text-2xl">
            {getCategoryIcon(category)}
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900">{availableCount}</div>
            <div className="text-xs text-gray-500">of {totalMachines}</div>
          </div>
        </div>
        
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900 capitalize">{category}</h3>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${availabilityPercentage}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500">
            <span>{availableCount} available</span>
            <span>{occupiedCount} in use</span>
            {offlineCount > 0 && <span>{offlineCount} offline</span>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}