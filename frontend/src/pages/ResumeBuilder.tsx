import { useState } from 'react';
import { 
  DocumentTextIcon, 
  SparklesIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  PlusIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

interface ResumeData {
  personalInfo: {
    fullName: string;
    email: string;
    phone: string;
    location: string;
    linkedin: string;
    portfolio: string;
  };
  summary: string;
  experience: Array<{
    id: string;
    company: string;
    position: string;
    startDate: string;
    endDate: string;
    current: boolean;
    description: string;
  }>;
  education: Array<{
    id: string;
    school: string;
    degree: string;
    field: string;
    graduationDate: string;
    gpa: string;
  }>;
  skills: string[];
  projects: Array<{
    id: string;
    name: string;
    description: string;
    technologies: string;
    link: string;
  }>;
}

const ResumeBuilder = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [resumeData, setResumeData] = useState<ResumeData>({
    personalInfo: {
      fullName: '',
      email: '',
      phone: '',
      location: '',
      linkedin: '',
      portfolio: ''
    },
    summary: '',
    experience: [],
    education: [],
    skills: [],
    projects: []
  });
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);

  const steps = [
    { id: 1, name: 'Personal Info', description: 'Basic information' },
    { id: 2, name: 'Summary', description: 'Professional summary' },
    { id: 3, name: 'Experience', description: 'Work experience' },
    { id: 4, name: 'Education', description: 'Educational background' },
    { id: 5, name: 'Skills', description: 'Technical & soft skills' },
    { id: 6, name: 'Projects', description: 'Portfolio projects' },
    { id: 7, name: 'Review', description: 'Preview & download' },
  ];

  const handlePersonalInfoChange = (field: string, value: string) => {
    setResumeData(prev => ({
      ...prev,
      personalInfo: {
        ...prev.personalInfo,
        [field]: value
      }
    }));
  };

  const addExperience = () => {
    const newExp = {
      id: Date.now().toString(),
      company: '',
      position: '',
      startDate: '',
      endDate: '',
      current: false,
      description: ''
    };
    setResumeData(prev => ({
      ...prev,
      experience: [...prev.experience, newExp]
    }));
  };

  const updateExperience = (id: string, field: string, value: string | boolean) => {
    setResumeData(prev => ({
      ...prev,
      experience: prev.experience.map(exp => 
        exp.id === id ? { ...exp, [field]: value } : exp
      )
    }));
  };

  const removeExperience = (id: string) => {
    setResumeData(prev => ({
      ...prev,
      experience: prev.experience.filter(exp => exp.id !== id)
    }));
  };

  const generateAISuggestions = async () => {
    setIsGeneratingAI(true);
    // Simulate AI API call
    setTimeout(() => {
      const suggestions = [
        "Consider highlighting your leadership experience in student organizations",
        "Add quantifiable achievements (e.g., 'Increased team productivity by 25%')",
        "Include relevant coursework that aligns with your target role",
        "Emphasize technical skills that are in high demand in your field"
      ];
      setAiSuggestions(suggestions);
      setIsGeneratingAI(false);
    }, 2000);
  };

  const renderPersonalInfoStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Full Name *
          </label>
          <input
            type="text"
            value={resumeData.personalInfo.fullName}
            onChange={(e) => handlePersonalInfoChange('fullName', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="John Doe"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email *
          </label>
          <input
            type="email"
            value={resumeData.personalInfo.email}
            onChange={(e) => handlePersonalInfoChange('email', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="john@example.com"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Number
          </label>
          <input
            type="tel"
            value={resumeData.personalInfo.phone}
            onChange={(e) => handlePersonalInfoChange('phone', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="+1 (555) 123-4567"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Location
          </label>
          <input
            type="text"
            value={resumeData.personalInfo.location}
            onChange={(e) => handlePersonalInfoChange('location', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="San Francisco, CA"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            LinkedIn URL
          </label>
          <input
            type="url"
            value={resumeData.personalInfo.linkedin}
            onChange={(e) => handlePersonalInfoChange('linkedin', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="https://linkedin.com/in/johndoe"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Portfolio/Website
          </label>
          <input
            type="url"
            value={resumeData.personalInfo.portfolio}
            onChange={(e) => handlePersonalInfoChange('portfolio', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="https://johndoe.dev"
          />
        </div>
      </div>
    </div>
  );

  const renderSummaryStep = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Professional Summary
        </label>
        <textarea
          value={resumeData.summary}
          onChange={(e) => setResumeData(prev => ({ ...prev, summary: e.target.value }))}
          rows={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          placeholder="Write a compelling summary that highlights your key strengths, experience, and career goals..."
        />
      </div>
      
      <div className="bg-blue-50 p-4 rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-medium text-blue-900 flex items-center">
            <SparklesIcon className="w-5 h-5 mr-2" />
            AI Suggestions
          </h3>
          <button
            onClick={() => generateAISuggestions()}
            disabled={isGeneratingAI}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            {isGeneratingAI ? 'Generating...' : 'Get AI Help'}
          </button>
        </div>
        {aiSuggestions.length > 0 && (
          <ul className="space-y-2">
            {aiSuggestions.map((suggestion, index) => (
              <li key={index} className="text-blue-800 text-sm">
                • {suggestion}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );

  const renderExperienceStep = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">Work Experience</h3>
        <button
          onClick={addExperience}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 flex items-center"
        >
          <PlusIcon className="w-4 h-4 mr-1" />
          Add Experience
        </button>
      </div>
      
      {resumeData.experience.map((exp) => (
        <div key={exp.id} className="border border-gray-200 rounded-lg p-6 relative">
          <button
            onClick={() => removeExperience(exp.id)}
            className="absolute top-4 right-4 text-red-600 hover:text-red-800"
          >
            <TrashIcon className="w-5 h-5" />
          </button>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company *
              </label>
              <input
                type="text"
                value={exp.company}
                onChange={(e) => updateExperience(exp.id, 'company', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Company Name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Position *
              </label>
              <input
                type="text"
                value={exp.position}
                onChange={(e) => updateExperience(exp.id, 'position', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                placeholder="Job Title"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="month"
                value={exp.startDate}
                onChange={(e) => updateExperience(exp.id, 'startDate', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="month"
                value={exp.endDate}
                onChange={(e) => updateExperience(exp.id, 'endDate', e.target.value)}
                disabled={exp.current}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              />
            </div>
          </div>
          
          <div className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={exp.current}
                onChange={(e) => updateExperience(exp.id, 'current', e.target.checked)}
                className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-sm text-gray-700">I currently work here</span>
            </label>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={exp.description}
              onChange={(e) => updateExperience(exp.id, 'description', e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Describe your responsibilities and achievements..."
            />
          </div>
        </div>
      ))}
      
      {resumeData.experience.length === 0 && (
        <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No experience added</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by adding your work experience.</p>
        </div>
      )}
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return renderPersonalInfoStep();
      case 2:
        return renderSummaryStep();
      case 3:
        return renderExperienceStep();
      case 4:
        return <div className="text-center py-12 text-gray-500">Education step coming soon...</div>;
      case 5:
        return <div className="text-center py-12 text-gray-500">Skills step coming soon...</div>;
      case 6:
        return <div className="text-center py-12 text-gray-500">Projects step coming soon...</div>;
      case 7:
        return <div className="text-center py-12 text-gray-500">Review step coming soon...</div>;
      default:
        return renderPersonalInfoStep();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Resume Builder</h1>
          <p className="text-gray-600">Create a professional resume with AI-powered suggestions</p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Steps Sidebar */}
          <div className="lg:w-64 flex-shrink-0">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-8">
              <nav className="space-y-1">
                {steps.map((step) => (
                  <button
                    key={step.id}
                    onClick={() => setCurrentStep(step.id)}
                    className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium ${
                      currentStep === step.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex items-center">
                      <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs mr-3 ${
                        currentStep === step.id
                          ? 'bg-blue-600 text-white'
                          : currentStep > step.id
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-300 text-gray-600'
                      }`}>
                        {step.id}
                      </span>
                      <div>
                        <div className="font-medium">{step.name}</div>
                        <div className="text-xs text-gray-500">{step.description}</div>
                      </div>
                    </div>
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            <div className="bg-white rounded-lg shadow-sm p-8">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  {steps.find(s => s.id === currentStep)?.name}
                </h2>
                <p className="text-gray-600">
                  {steps.find(s => s.id === currentStep)?.description}
                </p>
              </div>

              {renderCurrentStep()}

              {/* Navigation Buttons */}
              <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
                <button
                  onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
                  disabled={currentStep === 1}
                  className="px-6 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <div className="flex gap-3">
                  {currentStep === steps.length ? (
                    <>
                      <button className="px-6 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 flex items-center">
                        <EyeIcon className="w-4 h-4 mr-2" />
                        Preview
                      </button>
                      <button className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 flex items-center">
                        <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                        Download PDF
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setCurrentStep(Math.min(steps.length, currentStep + 1))}
                      className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                    >
                      Next
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeBuilder;
