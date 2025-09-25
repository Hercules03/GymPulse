import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
}

export const LegsIcon: React.FC<IconProps> = ({ className = "", size = 24 }) => (
  <img
    src="/icons/legpress.png"
    alt="Leg Press"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const ChestIcon: React.FC<IconProps> = ({ className = "", size = 24 }) => (
  <img
    src="/icons/benchpress.png"
    alt="Bench Press"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const BackIcon: React.FC<IconProps> = ({ className = "", size = 24 }) => (
  <img
    src="/icons/latpulldown.png"
    alt="Lat Pulldown"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const CardioIcon: React.FC<IconProps> = ({ className = "", size = 24 }) => (
  <img
    src="/icons/treadmill.png"
    alt="Treadmill"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const ArmsIcon: React.FC<IconProps> = ({ className = "", size = 24 }) => (
  <img
    src="/icons/dumbbell.png"
    alt="Dumbbell"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const OtherIcon: React.FC<IconProps> = ({ className = "", size = 24 }) => (
  <img
    src="/icons/kettlebell.png"
    alt="Kettlebell"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

// Map category names to icons
export const CategoryIconMap: Record<string, React.FC<IconProps>> = {
  legs: LegsIcon,
  chest: ChestIcon,
  back: BackIcon,
  cardio: CardioIcon,
  arms: ArmsIcon,
  other: OtherIcon,
};

// Helper function to get icon by category
export const getCategoryIcon = (category: string, props?: IconProps) => {
  const IconComponent = CategoryIconMap[category] || OtherIcon;
  return <IconComponent {...props} />;
};