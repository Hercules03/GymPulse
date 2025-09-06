import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Clock, Users, Navigation, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { createPageUrl } from '@/utils';

interface BranchRecommendation {
  branchId: string;
  name: string;
  eta: string;
  distance: string;
  availableCount: number;
  totalCount: number;
  category: string;
}

interface BranchRecommendationCardProps {
  recommendation: BranchRecommendation;
}

export default function BranchRecommendationCard({ recommendation }: BranchRecommendationCardProps) {
  const availabilityPercentage = (recommendation.availableCount / recommendation.totalCount) * 100;
  
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

  const getAvailabilityColor = (percentage: number) => {
    if (percentage >= 60) return 'text-green-600 bg-green-100';
    if (percentage >= 30) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getAvailabilityText = (available: number, total: number) => {
    if (available === 0) return 'Full';
    if (available === total) return 'Wide Open';
    if (available / total >= 0.6) return 'Good Availability';
    return 'Limited Space';
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer"
    >
      <Link to={createPageUrl(`Branches?branch=${recommendation.branchId}`)}>
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-lg">
              {getCategoryIcon(recommendation.category)}
            </div>
            <div>
              <h4 className="font-semibold text-gray-900">{recommendation.name}</h4>
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <MapPin className="w-3 h-3" />
                <span>{recommendation.distance} away</span>
              </div>
            </div>
          </div>
          
          {/* Availability Badge */}
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getAvailabilityColor(availabilityPercentage)}`}>
            {getAvailabilityText(recommendation.availableCount, recommendation.totalCount)}
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-4 mb-3">
          {/* ETA */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-blue-600 mb-1">
              <Clock className="w-4 h-4" />
            </div>
            <div className="text-lg font-bold text-gray-900">{recommendation.eta}</div>
            <div className="text-xs text-gray-500">Travel time</div>
          </div>

          {/* Available Equipment */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-green-600 mb-1">
              <CheckCircle className="w-4 h-4" />
            </div>
            <div className="text-lg font-bold text-gray-900">
              {recommendation.availableCount}/{recommendation.totalCount}
            </div>
            <div className="text-xs text-gray-500">Available</div>
          </div>

          {/* Category */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-purple-600 mb-1">
              <Users className="w-4 h-4" />
            </div>
            <div className="text-lg font-bold text-gray-900 capitalize">{recommendation.category}</div>
            <div className="text-xs text-gray-500">Equipment</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-3">
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div 
              className={`h-1.5 rounded-full transition-all duration-300 ${
                availabilityPercentage >= 60 ? 'bg-green-500' :
                availabilityPercentage >= 30 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${availabilityPercentage}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Equipment availability</span>
            <span>{Math.round(availabilityPercentage)}%</span>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex gap-2">
          <button className="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
            <Navigation className="w-4 h-4" />
            Get Directions
          </button>
          <button className="px-4 py-2 border border-gray-200 hover:border-gray-300 text-gray-600 hover:text-gray-800 rounded-lg text-sm font-medium transition-colors">
            View Details
          </button>
        </div>
      </Link>
    </motion.div>
  );
}