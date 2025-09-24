export interface BranchData {
  id: string;
  name: string;
  address: string;
  phone?: string;
  hours?: string;
  amenities?: string[];
}

export class Branch {
  id: string;
  name: string;
  address: string;
  phone?: string;
  hours?: string;
  amenities?: string[];

  constructor(data: BranchData) {
    this.id = data.id;
    this.name = data.name;
    this.address = data.address;
    this.phone = data.phone;
    this.hours = data.hours;
    this.amenities = data.amenities;
  }

  static async list(): Promise<Branch[]> {
    // Mock data for development
    const mockData: BranchData[] = [
      {
        id: 'downtown',
        name: 'Downtown',
        address: '123 Main St, Downtown',
        phone: '(555) 123-4567',
        hours: '24/7',
        amenities: ['Pool', 'Sauna', 'Personal Training']
      },
      {
        id: 'westside',
        name: 'Westside',
        address: '456 West Ave, Westside',
        phone: '(555) 234-5678',
        hours: '5AM - 11PM',
        amenities: ['Pool', 'Group Classes']
      },
      {
        id: 'north-campus',
        name: 'North Campus',
        address: '789 University Blvd, North Campus',
        phone: '(555) 345-6789',
        hours: '6AM - 10PM',
        amenities: ['Student Discounts', 'Study Areas']
      },
      {
        id: 'eastside',
        name: 'Eastside',
        address: '321 East St, Eastside',
        phone: '(555) 456-7890',
        hours: '24/7',
        amenities: ['Sauna', 'Personal Training', 'Childcare']
      }
    ];

    return mockData.map(data => new Branch(data));
  }
}
