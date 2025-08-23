import { Link } from 'react-router-dom';
import { 
  DocumentTextIcon, 
  BriefcaseIcon, 
  MicrophoneIcon,
  CurrencyDollarIcon,
  MapIcon,
  EnvelopeIcon
} from '@heroicons/react/24/outline';

const HomePage = () => {
  const features = [
    {
      name: 'AI Resume Builder',
      description: 'Create professional resumes with AI-powered suggestions and industry-specific optimizations.',
      href: '/resume',
      icon: DocumentTextIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Smart Job Matching',
      description: 'Find the perfect roles based on your skills, preferences, and market trends.',
      href: '/jobs',
      icon: BriefcaseIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Mock Interview Practice',
      description: 'Practice interviews with AI feedback on answers, tone, and body language.',
      href: '/interview',
      icon: MicrophoneIcon,
      color: 'bg-purple-500',
    },
    {
      name: 'Salary Insights',
      description: 'Get real-time salary data for your desired roles and locations.',
      href: '/salary',
      icon: CurrencyDollarIcon,
      color: 'bg-yellow-500',
    },
    {
      name: 'Career Roadmap',
      description: 'Get a personalized step-by-step guide to land your dream job.',
      href: '/roadmap',
      icon: MapIcon,
      color: 'bg-red-500',
    },
    {
      name: 'Email Automation',
      description: 'Send personalized emails to recruiters and mentors automatically.',
      href: '/email',
      icon: EnvelopeIcon,
      color: 'bg-indigo-500',
    },
  ];

  const stats = [
    { name: 'Students Helped', value: '10,000+' },
    { name: 'Job Placements', value: '2,500+' },
    { name: 'Average Salary Increase', value: '35%' },
    { name: 'Success Rate', value: '89%' },
  ];

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80">
          <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-blue-400 to-purple-600 opacity-30 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]" />
        </div>
        
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
              Land Your Dream Job with{' '}
              <span className="text-blue-600">AI-Powered</span> Career Tools
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              From resume building to interview preparation, get personalized AI assistance 
              throughout your job search journey. Join thousands of students who've successfully 
              launched their careers.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                to="/resume"
                className="rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
              >
                Get Started
              </Link>
              <Link
                to="/roadmap"
                className="text-sm font-semibold leading-6 text-gray-900"
              >
                View Career Roadmap <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-gray-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <dl className="grid grid-cols-1 gap-x-8 gap-y-16 text-center lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.name} className="mx-auto flex max-w-xs flex-col gap-y-4">
                <dt className="text-base leading-7 text-gray-600">{stat.name}</dt>
                <dd className="order-first text-3xl font-semibold tracking-tight text-gray-900 sm:text-5xl">
                  {stat.value}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-blue-600">
              AI-Powered Career Tools
            </h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need to land your dream job
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Our comprehensive suite of AI tools helps students at every stage of their job search, 
              from building the perfect resume to acing interviews.
            </p>
          </div>
          
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {features.map((feature) => (
                <div key={feature.name} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                    <div className={`h-10 w-10 flex items-center justify-center rounded-lg ${feature.color}`}>
                      <feature.icon className="h-6 w-6 text-white" aria-hidden="true" />
                    </div>
                    {feature.name}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">{feature.description}</p>
                    <p className="mt-6">
                      <Link
                        to={feature.href}
                        className="text-sm font-semibold leading-6 text-blue-600 hover:text-blue-500"
                      >
                        Try it now <span aria-hidden="true">→</span>
                      </Link>
                    </p>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600">
        <div className="px-6 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to supercharge your career?
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-blue-100">
              Join thousands of successful students who've used our AI-powered platform to land their dream jobs.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                to="/resume"
                className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-blue-600 shadow-sm hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                Start Building Resume
              </Link>
              <Link
                to="/jobs"
                className="text-sm font-semibold leading-6 text-white"
              >
                Find Jobs <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
