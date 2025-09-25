interface MapLegendProps {
  className?: string;
}

export default function MapLegend({ className }: MapLegendProps) {
  const legendItems = [
    { color: '#10b981', label: 'High Availability', range: '70%+' },
    { color: '#f59e0b', label: 'Medium Availability', range: '40-69%' },
    { color: '#ef4444', label: 'Low Availability', range: '0-39%' },
    { color: '#3b82f6', label: 'Your Location', range: '' }
  ];

  return (
    <div className={`absolute top-4 left-4 bg-white bg-opacity-90 backdrop-blur-sm rounded-lg shadow-lg border border-gray-200 p-3 z-10 ${className || ''}`}>
      <h4 className="text-sm font-semibold text-gray-800 mb-2">Availability Legend</h4>
      <div className="space-y-1.5">
        {legendItems.map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            <div className="flex items-center">
              {item.label === 'Your Location' ? (
                // User location marker
                <div className="w-4 h-4 rounded-full border-2 border-white shadow-sm" style={{ backgroundColor: item.color }}>
                  <svg
                    className="w-2 h-2 text-white ml-0.5 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>
                </div>
              ) : (
                // Branch pin marker
                <svg
                  width="16"
                  height="20"
                  viewBox="0 0 24 30"
                  className="drop-shadow-sm"
                >
                  <path
                    d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"
                    fill={item.color}
                    stroke="white"
                    strokeWidth="1"
                  />
                </svg>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium text-gray-700">{item.label}</div>
              {item.range && (
                <div className="text-xs text-gray-500">{item.range}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}