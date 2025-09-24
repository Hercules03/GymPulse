
import { MapPin } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface Location {
  id: string;
  name: string;
}

interface HeaderProps {
  selectedLocation: string;
  onLocationChange: (locationId: string) => void;
  locations: Location[];
}

export default function Header({ selectedLocation, onLocationChange, locations }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-100 px-6 py-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">FitTracker</h1>
          <p className="text-gray-500 text-sm mt-1">Real-time equipment monitoring</p>
        </div>
        
        <div className="flex items-center gap-3">
          <MapPin className="w-5 h-5 text-gray-400" />
          <Select value={selectedLocation} onValueChange={onLocationChange}>
            <SelectTrigger className="w-48 border-0 shadow-sm bg-gray-50 hover:bg-gray-100 transition-colors">
              <SelectValue placeholder="Select location" />
            </SelectTrigger>
            <SelectContent>
              {locations.map((location) => (
                <SelectItem key={location.id} value={location.id}>
                  {location.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
    </header>
  );
}