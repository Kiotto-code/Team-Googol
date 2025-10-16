export type Role = 'admin' | 'manager' | 'auditor' | 'viewer';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  roles: Role[];
  lastLoginAt?: string;
}
