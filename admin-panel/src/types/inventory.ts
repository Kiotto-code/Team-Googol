export interface Box {
  id: string;
  status: 'pending' | 'in_transit' | 'delivered' | 'exception';
  location: string;
  updatedAt: string;
  owner: string;
}

export interface CaseRecord {
  id: string;
  boxId: string;
  priority: 'low' | 'medium' | 'high';
  status: 'open' | 'investigating' | 'resolved';
  assignee: string;
  updatedAt: string;
}

export interface ItemRecord {
  id: string;
  name: string;
  sku: string;
  quantity: number;
  location: string;
  updatedAt: string;
}

export interface UserRecord {
  id: string;
  name: string;
  email: string;
  roles: string[];
  lastLoginAt: string;
  status: 'active' | 'suspended';
}

export interface AuditLog {
  id: string;
  actor: string;
  action: string;
  entity: string;
  createdAt: string;
  details?: string;
}
