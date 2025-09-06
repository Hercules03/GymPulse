import React from 'react';
import { Clock } from 'lucide-react';

interface PredictionChipProps {
  predictedFreeTime?: string;
  status: 'available' | 'occupied' | 'offline';
}

export default function PredictionChip({ predictedFreeTime, status }: PredictionChipProps) {
  if (status === 'available') {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-2 bg-green-50 text-green-700 rounded-lg text-sm">
        <Clock className="w-4 h-4" />
        <span>Ready to use</span>
      </div>
    );
  }

  if (status === 'offline') {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 text-gray-700 rounded-lg text-sm">
        <Clock className="w-4 h-4" />
        <span>Currently offline</span>
      </div>
    );
  }

  if (status === 'occupied' && predictedFreeTime) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-2 bg-orange-50 text-orange-700 rounded-lg text-sm">
        <Clock className="w-4 h-4" />
        <span>Available in ~{predictedFreeTime}</span>
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-2 px-3 py-2 bg-orange-50 text-orange-700 rounded-lg text-sm">
      <Clock className="w-4 h-4" />
      <span>Currently in use</span>
    </div>
  );
}