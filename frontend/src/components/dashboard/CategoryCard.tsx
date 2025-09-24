import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { getCategoryIcon } from "@/components/icons/CategoryIcons";

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
  // Get appropriate color scheme for each category
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'legs':
        return 'bg-blue-50 text-blue-600';
      case 'chest':
        return 'bg-red-50 text-red-600';
      case 'back':
        return 'bg-green-50 text-green-600';
      case 'cardio':
        return 'bg-purple-50 text-purple-600';
      case 'arms':
        return 'bg-orange-50 text-orange-600';
      default:
        return 'bg-gray-50 text-gray-600';
    }
  };

  const availabilityPercentage = totalMachines > 0 ? (availableCount / totalMachines) * 100 : 0;

  return (
    <Card className="border-0 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer h-full">
      <CardContent className="px-4 py-12">
        <div className="flex items-center justify-between mb-8">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${getCategoryColor(category)}`}>
            {getCategoryIcon(category, { size: 24 })}
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900">{availableCount}</div>
            <div className="text-xs text-gray-500">of {totalMachines}</div>
          </div>
        </div>

        <div className="space-y-4">
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