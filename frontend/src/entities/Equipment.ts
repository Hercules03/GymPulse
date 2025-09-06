export interface EquipmentData {
  machine_id: string;
  name: string;
  category: 'legs' | 'chest' | 'back' | 'cardio' | 'arms';
  status: 'available' | 'occupied' | 'offline';
  location: string;
  last_updated?: string;
  estimated_free_time?: string;
}

export class Equipment {
  machine_id: string;
  name: string;
  category: 'legs' | 'chest' | 'back' | 'cardio' | 'arms';
  status: 'available' | 'occupied' | 'offline';
  location: string;
  last_updated?: string;
  estimated_free_time?: string;

  constructor(data: EquipmentData) {
    this.machine_id = data.machine_id;
    this.name = data.name;
    this.category = data.category;
    this.status = data.status;
    this.location = data.location;
    this.last_updated = data.last_updated;
    this.estimated_free_time = data.estimated_free_time;
  }

  static async filter(params: { location?: string; category?: string; status?: string }): Promise<Equipment[]> {
    // Mock data for development - replace with actual API call
    const mockData: EquipmentData[] = [
      {
        machine_id: 'leg_press_001',
        name: 'Leg Press Machine',
        category: 'legs',
        status: 'available',
        location: params.location || 'Downtown',
        last_updated: new Date().toISOString(),
      },
      {
        machine_id: 'bench_press_001',
        name: 'Bench Press',
        category: 'chest',
        status: 'occupied',
        location: params.location || 'Downtown',
        last_updated: new Date().toISOString(),
        estimated_free_time: '10 mins'
      },
      {
        machine_id: 'lat_pulldown_001',
        name: 'Lat Pulldown',
        category: 'back',
        status: 'available',
        location: params.location || 'Downtown',
        last_updated: new Date().toISOString(),
      },
      {
        machine_id: 'squat_rack_001',
        name: 'Squat Rack',
        category: 'legs',
        status: 'offline',
        location: params.location || 'Downtown',
        last_updated: new Date().toISOString(),
      },
      {
        machine_id: 'chest_fly_001',
        name: 'Chest Fly Machine',
        category: 'chest',
        status: 'available',
        location: params.location || 'Downtown',
        last_updated: new Date().toISOString(),
      },
      {
        machine_id: 'back_extension_001',
        name: 'Back Extension',
        category: 'back',
        status: 'occupied',
        location: params.location || 'Downtown',
        last_updated: new Date().toISOString(),
        estimated_free_time: '5 mins'
      }
    ];

    let filtered = mockData;
    
    if (params.location) {
      filtered = filtered.filter(item => item.location === params.location);
    }
    
    if (params.category) {
      filtered = filtered.filter(item => item.category === params.category);
    }
    
    if (params.status) {
      filtered = filtered.filter(item => item.status === params.status);
    }

    return filtered.map(data => new Equipment(data));
  }

  static async findById(id: string): Promise<Equipment | null> {
    const allEquipment = await Equipment.filter({});
    return allEquipment.find(eq => eq.machine_id === id) || null;
  }
}
