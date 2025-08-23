import { useState } from 'react';
import { CheckCircleIcon, MapIcon, CalendarIcon } from '@heroicons/react/24/outline';

const Roadmap = () => {
  const [userProfile] = useState({
    name: 'John Doe',
    major: 'Computer Science',
    year: 'Junior',
    targetRole: 'Software Engineer',
    skills: ['JavaScript', 'React', 'Python']
  });

  const roadmapSteps = [
    {
      id: 1,
      title: 'Complete Your Resume',
      description: 'Build a professional resume with AI assistance',
      status: 'completed',
      dueDate: '2024-01-15',
      estimatedTime: '2 hours'
    },
    {
      id: 2,
      title: 'Build Portfolio Projects',
      description: 'Create 3-4 projects showcasing your skills',
      status: 'in-progress',
      dueDate: '2024-02-01',
      estimatedTime: '40 hours'
    },
    {
      id: 3,
      title: 'Practice Technical Interviews',
      description: 'Complete mock interviews and coding challenges',
      status: 'pending',
      dueDate: '2024-02-15',
      estimatedTime: '20 hours'
    },
    {
      id: 4,
      title: 'Apply to Companies',
      description: 'Submit applications to 20+ target companies',
      status: 'pending',
      dueDate: '2024-03-01',
      estimatedTime: '10 hours'
    },
    {
      id: 5,
      title: 'Network with Professionals',
      description: 'Connect with 50+ professionals in your field',
      status: 'pending',
      dueDate: '2024-03-15',
      estimatedTime: '15 hours'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'in-progress':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-6 h-6 text-green-600" />;
      case 'in-progress':
        return <div className="w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />;
      default:
        return <div className="w-6 h-6 border-2 border-gray-300 rounded-full" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Career Roadmap</h1>
          <p className="text-gray-600">Your personalized path to landing your dream job</p>
        </div>

        {/* Profile Summary */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-500">Name</div>
              <div className="font-semibold">{userProfile.name}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Major</div>
              <div className="font-semibold">{userProfile.major}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Academic Year</div>
              <div className="font-semibold">{userProfile.year}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Target Role</div>
              <div className="font-semibold">{userProfile.targetRole}</div>
            </div>
          </div>
        </div>

        {/* Progress Overview */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Progress Overview</h2>
          <div className="flex items-center mb-4">
            <div className="flex-1 bg-gray-200 rounded-full h-3">
              <div className="bg-blue-600 h-3 rounded-full" style={{ width: '20%' }}></div>
            </div>
            <span className="ml-3 text-sm text-gray-600">1 of 5 completed</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">1</div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">1</div>
              <div className="text-sm text-gray-600">In Progress</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">3</div>
              <div className="text-sm text-gray-600">Upcoming</div>
            </div>
          </div>
        </div>

        {/* Roadmap Steps */}
        <div className="space-y-6">
          {roadmapSteps.map((step, index) => (
            <div key={step.id} className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-start">
                <div className="flex-shrink-0 mr-4">
                  {getStatusIcon(step.status)}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
                      <p className="text-gray-600 mt-1">{step.description}</p>
                      <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                        <div className="flex items-center">
                          <CalendarIcon className="w-4 h-4 mr-1" />
                          Due: {new Date(step.dueDate).toLocaleDateString()}
                        </div>
                        <div className="flex items-center">
                          <MapIcon className="w-4 h-4 mr-1" />
                          Estimated: {step.estimatedTime}
                        </div>
                      </div>
                    </div>
                    <div className="ml-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(step.status)}`}>
                        {step.status.charAt(0).toUpperCase() + step.status.slice(1).replace('-', ' ')}
                      </span>
                    </div>
                  </div>
                  
                  {step.status !== 'completed' && (
                    <div className="mt-4">
                      <button className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700">
                        {step.status === 'in-progress' ? 'Continue' : 'Start'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
              
              {index < roadmapSteps.length - 1 && (
                <div className="ml-3 mt-4">
                  <div className="w-px h-8 bg-gray-200"></div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Next Steps */}
        <div className="bg-blue-50 rounded-lg p-6 mt-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">Next Steps</h3>
          <p className="text-blue-800 mb-4">
            Focus on building your portfolio projects. This is the most impactful step for your career success.
          </p>
          <button className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700">
            Get Started on Portfolio
          </button>
        </div>
      </div>
    </div>
  );
};

export default Roadmap;
