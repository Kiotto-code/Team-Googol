import { useState } from 'react';
import { EnvelopeIcon, UserGroupIcon, SparklesIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';

const EmailAutomation = () => {
  const [emailType, setEmailType] = useState('recruiter');
  const [emailData, setEmailData] = useState({
    recipient: '',
    company: '',
    position: '',
    subject: '',
    content: ''
  });
  const [isGenerating, setIsGenerating] = useState(false);

  const generateEmail = () => {
    setIsGenerating(true);
    // Simulate AI email generation
    setTimeout(() => {
      const templates = {
        recruiter: {
          subject: `Interest in ${emailData.position} Position at ${emailData.company}`,
          content: `Dear ${emailData.recipient},

I hope this email finds you well. I am writing to express my strong interest in the ${emailData.position} position at ${emailData.company}.

As a computer science student with experience in JavaScript, React, and Python, I am excited about the opportunity to contribute to your team. I have been following ${emailData.company}'s work and am particularly impressed by your recent projects.

I would love to discuss how my skills and enthusiasm can contribute to your team's success. I have attached my resume for your review.

Thank you for your time and consideration. I look forward to hearing from you.

Best regards,
John Doe`
        },
        mentor: {
          subject: `Seeking Mentorship in Software Development`,
          content: `Dear ${emailData.recipient},

I hope you're doing well. I came across your profile and was impressed by your experience in the tech industry.

I am currently a computer science student looking to break into the software development field. I would be honored to learn from your expertise and would greatly appreciate any guidance you could provide.

Would you be open to a brief coffee chat or virtual meeting? I'm happy to work around your schedule.

Thank you for considering my request.

Best regards,
John Doe`
        }
      };
      
      const template = templates[emailType as keyof typeof templates];
      setEmailData(prev => ({
        ...prev,
        subject: template.subject,
        content: template.content
      }));
      setIsGenerating(false);
    }, 2000);
  };

  const sendEmail = () => {
    // Simulate sending email
    alert('Email sent successfully!');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Email Automation</h1>
          <p className="text-gray-600">Send personalized emails to recruiters and mentors automatically</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Email Configuration */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Email Type</h3>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setEmailType('recruiter')}
                  className={`p-4 rounded-lg border-2 text-center transition-colors ${
                    emailType === 'recruiter'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <EnvelopeIcon className="w-8 h-8 mx-auto mb-2" />
                  <div className="font-medium">Recruiter</div>
                  <div className="text-sm text-gray-500">Job application emails</div>
                </button>
                <button
                  onClick={() => setEmailType('mentor')}
                  className={`p-4 rounded-lg border-2 text-center transition-colors ${
                    emailType === 'mentor'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <UserGroupIcon className="w-8 h-8 mx-auto mb-2" />
                  <div className="font-medium">Mentor</div>
                  <div className="text-sm text-gray-500">Networking emails</div>
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Email Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Recipient Name
                  </label>
                  <input
                    type="text"
                    value={emailData.recipient}
                    onChange={(e) => setEmailData({...emailData, recipient: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Jane Smith"
                  />
                </div>
                
                {emailType === 'recruiter' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Company Name
                      </label>
                      <input
                        type="text"
                        value={emailData.company}
                        onChange={(e) => setEmailData({...emailData, company: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Google"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Position
                      </label>
                      <input
                        type="text"
                        value={emailData.position}
                        onChange={(e) => setEmailData({...emailData, position: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Software Engineer"
                      />
                    </div>
                  </>
                )}
                
                <button
                  onClick={generateEmail}
                  disabled={isGenerating}
                  className="w-full bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 font-medium flex items-center justify-center disabled:opacity-50"
                >
                  <SparklesIcon className="w-5 h-5 mr-2" />
                  {isGenerating ? 'Generating...' : 'Generate AI Email'}
                </button>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Email Templates</h3>
              <div className="space-y-3">
                <div className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <div className="font-medium text-gray-900">Professional Introduction</div>
                  <div className="text-sm text-gray-500">Formal introduction with background</div>
                </div>
                <div className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <div className="font-medium text-gray-900">Follow-up Email</div>
                  <div className="text-sm text-gray-500">Following up on previous conversation</div>
                </div>
                <div className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                  <div className="font-medium text-gray-900">Thank You Note</div>
                  <div className="text-sm text-gray-500">After interview or meeting</div>
                </div>
              </div>
            </div>
          </div>

          {/* Email Preview */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Email Preview</h3>
              <button
                onClick={sendEmail}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center text-sm"
              >
                <PaperAirplaneIcon className="w-4 h-4 mr-2" />
                Send Email
              </button>
            </div>

            <div className="border border-gray-200 rounded-lg">
              <div className="border-b border-gray-200 p-4 bg-gray-50">
                <div className="space-y-2">
                  <div className="flex">
                    <span className="text-sm font-medium text-gray-500 w-16">To:</span>
                    <span className="text-sm text-gray-900">{emailData.recipient || 'recipient@example.com'}</span>
                  </div>
                  <div className="flex">
                    <span className="text-sm font-medium text-gray-500 w-16">Subject:</span>
                    <input
                      type="text"
                      value={emailData.subject}
                      onChange={(e) => setEmailData({...emailData, subject: e.target.value})}
                      className="text-sm text-gray-900 border-none bg-transparent flex-1 focus:outline-none"
                      placeholder="Email subject..."
                    />
                  </div>
                </div>
              </div>
              
              <div className="p-4">
                <textarea
                  value={emailData.content}
                  onChange={(e) => setEmailData({...emailData, content: e.target.value})}
                  rows={16}
                  className="w-full border-none resize-none focus:outline-none text-gray-900"
                  placeholder="Email content will appear here..."
                />
              </div>
            </div>

            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start">
                <SparklesIcon className="w-5 h-5 text-blue-600 mr-2 mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-blue-900">AI Tips</div>
                  <div className="text-sm text-blue-800 mt-1">
                    • Keep your email concise and to the point<br/>
                    • Personalize each email with specific company details<br/>
                    • Include a clear call-to-action<br/>
                    • Proofread before sending
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Email History */}
        <div className="mt-8 bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Emails</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recipient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Subject
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sent Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">john.doe@techcorp.com</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">Interest in Software Engineer Position</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Recruiter</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                      Sent
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Jan 15, 2024</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailAutomation;
