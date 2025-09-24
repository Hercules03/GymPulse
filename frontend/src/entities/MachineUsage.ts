export interface MachineUsageData {
  machine_id: string;
  hour: number;
  day_of_week: number;
  average_usage: number;
  predicted_free_time?: string;
}

export class MachineUsage {
  machine_id: string;
  hour: number;
  day_of_week: number;
  average_usage: number;
  predicted_free_time?: string;

  constructor(data: MachineUsageData) {
    this.machine_id = data.machine_id;
    this.hour = data.hour;
    this.day_of_week = data.day_of_week;
    this.average_usage = data.average_usage;
    this.predicted_free_time = data.predicted_free_time;
  }

  static async filter(params: { machine_id?: string }): Promise<MachineUsage[]> {
    // Mock usage data for development
    const mockData: MachineUsageData[] = [];
    
    // Generate 24 hours of mock data for the machine
    for (let hour = 0; hour < 24; hour++) {
      // Simulate higher usage during peak hours (6-9 AM, 5-8 PM)
      let baseUsage = 0.3;
      if ((hour >= 6 && hour <= 9) || (hour >= 17 && hour <= 20)) {
        baseUsage = 0.8;
      } else if ((hour >= 10 && hour <= 16) || (hour >= 21 && hour <= 22)) {
        baseUsage = 0.5;
      }
      
      // Add some randomness
      const usage = Math.min(1, baseUsage + (Math.random() - 0.5) * 0.3);
      
      mockData.push({
        machine_id: params.machine_id || 'default',
        hour,
        day_of_week: new Date().getDay(),
        average_usage: usage,
        predicted_free_time: usage > 0.7 ? `${Math.floor(Math.random() * 30 + 5)} mins` : undefined
      });
    }

    return mockData.map(data => new MachineUsage(data));
  }
}
