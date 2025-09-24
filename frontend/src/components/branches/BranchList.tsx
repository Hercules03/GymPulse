import React from 'react';
import { motion } from 'framer-motion';
import BranchCard from './BranchCard';

interface Branch {
  id: string;
  name: string;
  address: string;
  phone?: string;
  hours?: string;
  amenities?: string[];
  totalMachines: number;
  availableMachines: number;
  availability: number;
  distance: string;
  eta: number;
}

interface BranchListProps {
  branches: Branch[];
  isLoading: boolean;
  onBranchNavigate?: () => void;
}

export default function BranchList({ branches, isLoading, onBranchNavigate }: BranchListProps) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="animate-pulse">
            <div className="bg-white rounded-lg p-6 border border-gray-100">
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                <div className="h-2 bg-gray-200 rounded w-full"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (branches.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No branches found matching your search.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {branches.map((branch, index) => (
        <motion.div
          key={branch.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
        >
          <BranchCard branch={branch} onNavigate={onBranchNavigate} />
        </motion.div>
      ))}
    </div>
  );
}