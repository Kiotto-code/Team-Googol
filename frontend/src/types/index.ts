export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  salary: string;
  matchScore: number;
  posted: string;
  description: string;
  requirements: string[];
  type: string;
}

export interface ResumeData {
  personalInfo: {
    fullName: string;
    email: string;
    phone: string;
    location: string;
    linkedin: string;
    portfolio: string;
  };
  summary: string;
  experience: Experience[];
  education: Education[];
  skills: string[];
  projects: Project[];
}

export interface Experience {
  id: string;
  company: string;
  position: string;
  startDate: string;
  endDate: string;
  current: boolean;
  description: string;
}

export interface Education {
  id: string;
  school: string;
  degree: string;
  field: string;
  graduationDate: string;
  gpa: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  technologies: string;
  link: string;
}

export interface InterviewFeedback {
  overallScore: number;
  strengths: string[];
  improvements: string[];
  bodyLanguage: {
    score: number;
    notes: string;
  };
  speechPattern: {
    score: number;
    notes: string;
  };
}

export interface SalaryData {
  id: number;
  title: string;
  avgSalary: string;
  range: string;
  location: string;
  companies: string[];
  trend: string;
}
