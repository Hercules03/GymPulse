// Professional SVG icons for GymPulse categories
export {
  LegsIcon,
  ChestIcon,
  BackIcon,
  CardioIcon,
  ArmsIcon,
  CategoryIconMap,
  getCategoryIcon
} from './CategoryIcons';

// Category color schemes
export const CategoryColors = {
  legs: 'bg-blue-50 text-blue-600',
  chest: 'bg-red-50 text-red-600',
  back: 'bg-green-50 text-green-600',
  cardio: 'bg-purple-50 text-purple-600',
  arms: 'bg-orange-50 text-orange-600',
  default: 'bg-gray-50 text-gray-600'
} as const;

export type CategoryType = keyof typeof CategoryColors;