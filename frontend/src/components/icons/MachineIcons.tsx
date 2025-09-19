import React from 'react';

interface MachineIconProps {
  className?: string;
  size?: number;
}

// Machine-specific icon components
export const LegPressIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/legpress.png"
    alt="Leg Press Machine"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const BenchPressIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/benchpress.png"
    alt="Bench Press"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const ChestPressIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/chest-press.png"
    alt="Chest Press Machine"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const LatPulldownIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/latpulldown.png"
    alt="Lat Pulldown Machine"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const CableRowIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/cableroll.png"
    alt="Cable Row Machine"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const PullUpBarIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/pullupbar.png"
    alt="Pull-up Bar"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const SquatRackIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/squat-rack.png"
    alt="Squat Rack"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const SmithMachineIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/smithmachine.png"
    alt="Smith Machine"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const DumbbellIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/dumbbell.png"
    alt="Dumbbell"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const PreacherCurlIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/preacher-curl-bench.png"
    alt="Preacher Curl Bench"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const TreadmillIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/treadmill.png"
    alt="Treadmill"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const EllipticalIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/elliptical.png"
    alt="Elliptical Machine"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const StationaryBikeIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/stationary-bike.png"
    alt="Stationary Bike"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const CableCrossoverIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/cablecrossover.png"
    alt="Cable Crossover"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const KettlebellIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/kettlebell.png"
    alt="Kettlebell"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

export const BattleRopeIcon: React.FC<MachineIconProps> = ({ className = "", size = 32 }) => (
  <img
    src="/icons/battle-rope.png"
    alt="Battle Rope"
    width={size}
    height={size}
    className={className}
    style={{ objectFit: 'contain' }}
  />
);

// Machine type to icon mapping
export const MachineIconMap: Record<string, React.FC<MachineIconProps>> = {
  // Legs Equipment
  'leg-press': LegPressIcon,
  'leg_press': LegPressIcon,
  'legpress': LegPressIcon,
  'squat-rack': SquatRackIcon,
  'squat_rack': SquatRackIcon,
  'smith-machine': SmithMachineIcon,
  'smith_machine': SmithMachineIcon,

  // Chest Equipment
  'bench-press': BenchPressIcon,
  'bench_press': BenchPressIcon,
  'benchpress': BenchPressIcon,
  'chest-press': ChestPressIcon,
  'chest_press': ChestPressIcon,
  'cable-crossover': CableCrossoverIcon,
  'cable_crossover': CableCrossoverIcon,

  // Back Equipment
  'lat-pulldown': LatPulldownIcon,
  'lat_pulldown': LatPulldownIcon,
  'latpulldown': LatPulldownIcon,
  'cable-row': CableRowIcon,
  'cable_row': CableRowIcon,
  'cablerow': CableRowIcon,
  'rowing': CableRowIcon,
  'row': CableRowIcon,
  'pull-up': PullUpBarIcon,
  'pull_up': PullUpBarIcon,
  'pullup': PullUpBarIcon,
  'pull-up-bar': PullUpBarIcon,
  't-bar-row': CableRowIcon,
  't_bar_row': CableRowIcon,
  'tbar-row': CableRowIcon,
  'tbarrow': CableRowIcon,

  // Arms Equipment
  'dumbbell': DumbbellIcon,
  'preacher-curl': PreacherCurlIcon,
  'preacher_curl': PreacherCurlIcon,

  // Cardio Equipment
  'treadmill': TreadmillIcon,
  'elliptical': EllipticalIcon,
  'stationary-bike': StationaryBikeIcon,
  'stationary_bike': StationaryBikeIcon,
  'exercise-bike': StationaryBikeIcon,
  'exercise_bike': StationaryBikeIcon,

  // Other Equipment
  'kettlebell': KettlebellIcon,
  'battle-rope': BattleRopeIcon,
  'battle_rope': BattleRopeIcon,
};

// Helper function to get machine icon by type/name
export const getMachineIcon = (machineType: string, machineName?: string, props?: MachineIconProps) => {
  // Try to match by machine type first
  let IconComponent = MachineIconMap[machineType.toLowerCase()];

  // If not found, try to match by machine name
  if (!IconComponent && machineName) {
    // Try multiple name transformations
    const nameVariants = [
      machineName.toLowerCase().replace(/\s+/g, '-').replace(/machine.*$/, '').replace(/\d+$/, '').trim(),
      machineName.toLowerCase().replace(/\s+/g, '_').replace(/machine.*$/, '').replace(/\d+$/, '').trim(),
      machineName.toLowerCase().replace(/\s+/g, '').replace(/machine.*$/, '').replace(/\d+$/, '').trim(),
      machineName.toLowerCase().replace(/\s+.*$/, '').trim() // Just the first word
    ];

    for (const nameKey of nameVariants) {
      IconComponent = MachineIconMap[nameKey];
      if (IconComponent) {
        break;
      }
    }
  }

  // Default to dumbbell icon if no match found
  IconComponent = IconComponent || DumbbellIcon;

  return <IconComponent {...props} />;
};