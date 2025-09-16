import React, { useState } from 'react';
import { Bell, BellRing } from 'lucide-react';

interface NotificationButtonProps {
  machineId: string;
  status: 'available' | 'free' | 'occupied' | 'offline' | 'unknown';
}

export default function NotificationButton({ machineId, status }: NotificationButtonProps) {
  const [isSubscribed, setIsSubscribed] = useState(false);

  const handleNotificationToggle = () => {
    if (isSubscribed) {
      // Unsubscribe logic
      setIsSubscribed(false);
      console.log(`Unsubscribed from notifications for machine ${machineId}`);
    } else {
      // Subscribe logic
      setIsSubscribed(true);
      console.log(`Subscribed to notifications for machine ${machineId}`);
    }
  };

  if (status === 'available' || status === 'free') {
    return null; // Don't show notification button for available machines
  }

  return (
    <button
      onClick={handleNotificationToggle}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
        isSubscribed
          ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {isSubscribed ? (
        <>
          <BellRing className="w-4 h-4" />
          <span>Notifications On</span>
        </>
      ) : (
        <>
          <Bell className="w-4 h-4" />
          <span>Notify When Free</span>
        </>
      )}
    </button>
  );
}