import { useState } from 'react';
import { MicrophoneIcon, VideoCameraIcon, PlayIcon, StopIcon } from '@heroicons/react/24/outline';
import type { InterviewFeedback } from '../types';

const MockInterview = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [interviewType, setInterviewType] = useState('behavioral');
  const [feedback, setFeedback] = useState<InterviewFeedback | null>(null);

  const questions = {
    behavioral: [
      "Tell me about yourself and why you're interested in this position.",
      "Describe a challenging project you worked on and how you overcame obstacles.",
      "Tell me about a time when you had to work with a difficult team member.",
      "Where do you see yourself in 5 years?",
      "Why should we hire you over other candidates?"
    ],
    technical: [
      "Explain the difference between let, const, and var in JavaScript.",
      "How would you optimize a slow database query?",
      "Describe the concept of object-oriented programming.",
      "What is the difference between SQL and NoSQL databases?",
      "How would you handle authentication in a web application?"
    ],
    situational: [
      "How would you handle a situation where you disagree with your manager?",
      "What would you do if you realized you made a mistake in production?",
      "How would you prioritize tasks when everything seems urgent?",
      "How would you handle a situation with an unrealistic deadline?",
      "What would you do if a client was unhappy with your work?"
    ]
  };

  const startInterview = () => {
    setCurrentQuestion(0);
    setFeedback(null);
  };

  const nextQuestion = () => {
    if (currentQuestion < questions[interviewType as keyof typeof questions].length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const generateFeedback = () => {
    // Simulate AI feedback generation
    setTimeout(() => {
      setFeedback({
        overallScore: 85,
        strengths: [
          "Clear and confident communication",
          "Good use of specific examples",
          "Professional tone throughout"
        ],
        improvements: [
          "Could provide more quantifiable achievements",
          "Consider using the STAR method more consistently",
          "Work on reducing filler words"
        ],
        bodyLanguage: {
          score: 90,
          notes: "Excellent eye contact and posture"
        },
        speechPattern: {
          score: 80,
          notes: "Good pace, but could vary tone more"
        }
      });
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Mock Interview</h1>
          <p className="text-gray-600">Practice interviews with AI-powered feedback</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Interview Setup */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Interview Type</h3>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="behavioral"
                    checked={interviewType === 'behavioral'}
                    onChange={(e) => setInterviewType(e.target.value)}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <span className="text-gray-700">Behavioral</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="technical"
                    checked={interviewType === 'technical'}
                    onChange={(e) => setInterviewType(e.target.value)}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <span className="text-gray-700">Technical</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="situational"
                    checked={interviewType === 'situational'}
                    onChange={(e) => setInterviewType(e.target.value)}
                    className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                  <span className="text-gray-700">Situational</span>
                </label>
              </div>
              
              <button
                onClick={startInterview}
                className="w-full mt-6 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 font-medium flex items-center justify-center"
              >
                <PlayIcon className="w-4 h-4 mr-2" />
                Start Interview
              </button>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Question Progress</h3>
              <div className="space-y-2">
                {questions[interviewType as keyof typeof questions].map((_, index) => (
                  <div
                    key={index}
                    className={`w-full h-2 rounded-full ${
                      index <= currentQuestion ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  />
                ))}
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Question {currentQuestion + 1} of {questions[interviewType as keyof typeof questions].length}
              </p>
            </div>
          </div>

          {/* Main Interview Area */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
              <div className="text-center mb-8">
                <div className="w-32 h-32 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <VideoCameraIcon className="w-16 h-16 text-gray-400" />
                </div>
                <p className="text-sm text-gray-500">Your video will appear here</p>
              </div>

              <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Current Question:</h2>
                <div className="bg-blue-50 p-6 rounded-lg">
                  <p className="text-lg text-gray-800">
                    {questions[interviewType as keyof typeof questions][currentQuestion]}
                  </p>
                </div>
              </div>

              <div className="flex justify-center space-x-4 mb-6">
                <button
                  onClick={() => setIsRecording(!isRecording)}
                  className={`flex items-center px-6 py-3 rounded-lg font-medium ${
                    isRecording
                      ? 'bg-red-600 text-white hover:bg-red-700'
                      : 'bg-green-600 text-white hover:bg-green-700'
                  }`}
                >
                  {isRecording ? (
                    <>
                      <StopIcon className="w-5 h-5 mr-2" />
                      Stop Recording
                    </>
                  ) : (
                    <>
                      <MicrophoneIcon className="w-5 h-5 mr-2" />
                      Start Recording
                    </>
                  )}
                </button>
              </div>

              <div className="flex justify-between">
                <button
                  onClick={previousQuestion}
                  disabled={currentQuestion === 0}
                  className="px-6 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                
                <button
                  onClick={generateFeedback}
                  className="px-6 py-2 bg-purple-600 text-white rounded-md text-sm font-medium hover:bg-purple-700"
                >
                  Get AI Feedback
                </button>

                <button
                  onClick={nextQuestion}
                  disabled={currentQuestion === questions[interviewType as keyof typeof questions].length - 1}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>

            {/* Feedback Section */}
            {feedback && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">AI Feedback</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">{feedback.overallScore}%</div>
                    <div className="text-sm text-gray-600">Overall Score</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">{feedback.bodyLanguage.score}%</div>
                    <div className="text-sm text-gray-600">Body Language</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600">{feedback.speechPattern.score}%</div>
                    <div className="text-sm text-gray-600">Speech Pattern</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-lg font-medium text-green-700 mb-3">Strengths</h4>
                    <ul className="space-y-2">
                      {feedback.strengths.map((strength: string, index: number) => (
                        <li key={index} className="flex items-start">
                          <span className="text-green-500 mr-2">✓</span>
                          <span className="text-gray-700">{strength}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="text-lg font-medium text-orange-700 mb-3">Areas for Improvement</h4>
                    <ul className="space-y-2">
                      {feedback.improvements.map((improvement: string, index: number) => (
                        <li key={index} className="flex items-start">
                          <span className="text-orange-500 mr-2">•</span>
                          <span className="text-gray-700">{improvement}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MockInterview;
