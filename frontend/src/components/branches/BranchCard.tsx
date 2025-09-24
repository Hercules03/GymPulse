import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { MapPin, Clock, Users } from 'lucide-react';

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

interface BranchCardProps {
  branch: Branch;
  onNavigate?: () => void;
}

export default function BranchCard({ branch, onNavigate }: BranchCardProps) {
  const navigate = useNavigate();

  const getAvailabilityColor = (percentage: number) => {
    if (percentage >= 70) return 'text-green-600 bg-green-50';
    if (percentage >= 40) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  const getAvailabilityLabel = (percentage: number) => {
    if (percentage >= 70) return 'High';
    if (percentage >= 40) return 'Medium';
    return 'Low';
  };

  const handleClick = () => {
    onNavigate?.(); // Call the callback to close bottom sheet if needed
    navigate(`/dashboard/${branch.id}`);
  };

  return (
    <Card
      className="border-0 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer"
      onClick={handleClick}
    >
      <CardContent className="px-4 py-10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">{branch.name}</h3>
            <div className="flex items-center gap-1 text-sm text-gray-500 mb-2">
              <MapPin className="w-4 h-4" />
              <span>{branch.address}</span>
            </div>
            {branch.hours && (
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                <span>{branch.hours}</span>
              </div>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${getAvailabilityColor(branch.availability)}`}>
              {getAvailabilityLabel(branch.availability)} Availability
            </div>
            <div className="text-xs text-gray-500">
              {branch.distance} km • {branch.eta} min
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 text-sm">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">
                {branch.availableMachines}/{branch.totalMachines} available
              </span>
            </div>
          </div>
          
          <div className="w-24 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${branch.availability}%` }}
            />
          </div>
        </div>

        {branch.amenities && branch.amenities.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <div className="flex flex-wrap gap-2">
              {branch.amenities.slice(0, 3).map((amenity, index) => (
                <span 
                  key={index}
                  className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                >
                  {amenity}
                </span>
              ))}
              {branch.amenities.length > 3 && (
                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                  +{branch.amenities.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}