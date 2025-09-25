interface MapLegendProps {
  className?: string;
}

export default function MapLegend({ className }: MapLegendProps) {
  const legendItems = [
    { color: '#10b981', label: 'High' },
    { color: '#f59e0b', label: 'Medium' },
    { color: '#ef4444', label: 'Low' },
    { color: '#3b82f6', label: 'You' }
  ];

  return (
    <div className={`absolute top-4 left-4 p-2 z-10 ${className || ''}`}>
      <div className="flex items-center gap-3">
        {legendItems.map((item, index) => (
          <div key={index} className="flex items-center gap-1">
            {item.label === 'You' ? (
              // User location marker
              <div className="w-3 h-3 rounded-full border border-white" style={{ backgroundColor: item.color }} />
            ) : (
              // Branch pin marker
              <svg width="12" height="15" viewBox="0 0 24 30">
                <path
                  d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
                  fill={item.color}
                  stroke="white"
                  strokeWidth="1"
                />
              </svg>
            )}
            <span className="text-xs font-medium text-gray-700">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}