import { useState } from 'react';
import { MapPinIcon } from '@heroicons/react/24/outline';

const SalaryInsights = () => {
  const [filters, setFilters] = useState({
    jobTitle: '',
    location: '',
    experienceLevel: 'entry',
    company: ''
  });

  const salaryData = [
    {
      id: 1,
      title: 'Frontend Developer',
      avgSalary: '$75,000',
      range: '$60,000 - $95,000',
      location: 'San Francisco, CA',
      companies: ['Google', 'Facebook', 'Airbnb'],
      trend: '+5.2%'
    },
    {
      id: 2,
      title: 'Software Engineer',
      avgSalary: '$85,000',
      range: '$70,000 - $110,000',
      location: 'New York, NY',
      companies: ['Microsoft', 'Goldman Sachs', 'JPMorgan'],
      trend: '+7.1%'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Salary Insights</h1>
          <p className="text-gray-600">Get real-time salary data for your career goals</p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          <div className="lg:w-80">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Search Filters</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Job Title</label>
                  <input
                    type="text"
                    value={filters.jobTitle}
                    onChange={(e) => setFilters({...filters, jobTitle: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="Software Engineer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                  <input
                    type="text"
                    value={filters.location}
                    onChange={(e) => setFilters({...filters, location: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    placeholder="San Francisco, CA"
                  />
                </div>
                <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700">
                  Search Salaries
                </button>
              </div>
            </div>
          </div>

          <div className="flex-1">
            <div className="space-y-6">
              {salaryData.map((job) => (
                <div key={job.id} className="bg-white rounded-lg shadow-sm p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
                      <div className="flex items-center text-gray-600 mt-1">
                        <MapPinIcon className="w-4 h-4 mr-1" />
                        {job.location}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-green-600">{job.avgSalary}</div>
                      <div className="text-sm text-gray-500">Average</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <div className="text-sm text-gray-500">Salary Range</div>
                      <div className="font-semibold">{job.range}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Year over Year</div>
                      <div className="font-semibold text-green-600">{job.trend}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Top Companies</div>
                      <div className="text-sm">{job.companies.slice(0, 2).join(', ')}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SalaryInsights;
