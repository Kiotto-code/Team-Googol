import { useState } from 'react';
import { BriefcaseIcon, MapPinIcon, CalendarIcon, StarIcon } from '@heroicons/react/24/outline';

const JobMatcher = () => {
  const [preferences, setPreferences] = useState({
    skills: '',
    location: '',
    jobType: 'full-time',
    salaryRange: '50000-80000',
    experience: 'entry'
  });

  const [matchedJobs] = useState([
    {
      id: 1,
      title: 'Frontend Developer',
      company: 'Tech Solutions Inc',
      location: 'San Francisco, CA',
      salary: '$70,000 - $90,000',
      matchScore: 95,
      posted: '2 days ago',
      description: 'Join our team to build amazing user experiences...',
      requirements: ['React', 'TypeScript', 'Tailwind CSS'],
      type: 'Full-time'
    },
    {
      id: 2,
      title: 'Software Engineer Intern',
      company: 'StartupXYZ',
      location: 'Remote',
      salary: '$20/hour',
      matchScore: 88,
      posted: '1 week ago',
      description: 'Great opportunity for students to gain experience...',
      requirements: ['JavaScript', 'Node.js', 'Git'],
      type: 'Internship'
    }
  ]);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Job Matcher</h1>
          <p className="text-gray-600">Find the perfect roles based on your skills and preferences</p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Filters Sidebar */}
          <div className="lg:w-80 flex-shrink-0">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Preferences</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Skills</label>
                  <input
                    type="text"
                    value={preferences.skills}
                    onChange={(e) => setPreferences({...preferences, skills: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="React, JavaScript, Python..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                  <input
                    type="text"
                    value={preferences.location}
                    onChange={(e) => setPreferences({...preferences, location: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="San Francisco, Remote..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Job Type</label>
                  <select
                    value={preferences.jobType}
                    onChange={(e) => setPreferences({...preferences, jobType: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="full-time">Full-time</option>
                    <option value="part-time">Part-time</option>
                    <option value="internship">Internship</option>
                    <option value="contract">Contract</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Experience Level</label>
                  <select
                    value={preferences.experience}
                    onChange={(e) => setPreferences({...preferences, experience: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="entry">Entry Level (0-2 years)</option>
                    <option value="mid">Mid Level (2-5 years)</option>
                    <option value="senior">Senior Level (5+ years)</option>
                  </select>
                </div>
                
                <button className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 font-medium">
                  Update Matches
                </button>
              </div>
            </div>
          </div>

          {/* Job Listings */}
          <div className="flex-1">
            <div className="mb-6 flex justify-between items-center">
              <p className="text-gray-600">{matchedJobs.length} jobs found</p>
              <select className="px-3 py-2 border border-gray-300 rounded-md">
                <option>Sort by Match Score</option>
                <option>Sort by Date Posted</option>
                <option>Sort by Salary</option>
              </select>
            </div>
            
            <div className="space-y-6">
              {matchedJobs.map((job) => (
                <div key={job.id} className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <h3 className="text-xl font-semibold text-gray-900 mr-3">{job.title}</h3>
                        <div className="flex items-center bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm font-medium">
                          <StarIcon className="w-4 h-4 mr-1" />
                          {job.matchScore}% match
                        </div>
                      </div>
                      <p className="text-lg text-gray-700 mb-2">{job.company}</p>
                      <div className="flex flex-wrap items-center text-sm text-gray-500 gap-4 mb-3">
                        <div className="flex items-center">
                          <MapPinIcon className="w-4 h-4 mr-1" />
                          {job.location}
                        </div>
                        <div className="flex items-center">
                          <BriefcaseIcon className="w-4 h-4 mr-1" />
                          {job.type}
                        </div>
                        <div className="flex items-center">
                          <CalendarIcon className="w-4 h-4 mr-1" />
                          Posted {job.posted}
                        </div>
                      </div>
                      <p className="text-gray-600 mb-3">{job.description}</p>
                      <div className="flex flex-wrap gap-2 mb-4">
                        {job.requirements.map((req, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                          >
                            {req}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right ml-6">
                      <p className="text-lg font-semibold text-gray-900 mb-2">{job.salary}</p>
                      <button className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 font-medium mb-2">
                        Apply Now
                      </button>
                      <br />
                      <button className="text-blue-600 hover:text-blue-800 text-sm">
                        Save Job
                      </button>
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

export default JobMatcher;
