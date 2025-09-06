import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Users, Clock, AlertTriangle } from 'lucide-react';

export default function QuickStats({ totalEquipment, totalAvailable, peakHours, maintenanceNeeded }) {
  const stats = [
    {
      label: 'Total Equipment',
      value: totalEquipment,
      icon: TrendingUp,
      color: 'text-blue-600',
      bg: 'bg-blue-50'
    },
    {
      label: 'Available Now',
      value: totalAvailable,
      icon: Users,
      color: 'text-green-600',
      bg: 'bg-green-50'
    },
    {
      label: 'Peak Hours',
      value: peakHours,
      icon: Clock,
      color: 'text-orange-600',
      bg: 'bg-orange-50'
    },
    {
      label: 'Maintenance',
      value: maintenanceNeeded,
      icon: AlertTriangle,
      color: 'text-red-600',
      bg: 'bg-red-50'
    }
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {stats.map((stat, index) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
        >
          <Card className="border-0 shadow-sm hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <div className={`w-10 h-10 rounded-lg ${stat.bg} flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}