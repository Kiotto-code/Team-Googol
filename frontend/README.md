# 🚀 AI-Integrated Hiring Web App

A comprehensive platform that helps university students land their dream jobs using AI-powered career tools.

## ✨ Features

### 🏠 **Homepage**
- Beautiful landing page with feature overview
- Success statistics and user testimonials
- Modern, responsive design

### 📄 **AI Resume Builder**
- Step-by-step resume creation process
- AI-powered suggestions and improvements
- Industry-standard templates
- Real-time preview and editing

### 🎯 **Smart Job Matcher**
- AI-powered job recommendations
- Skills-based matching algorithm
- Filter by location, salary, and job type
- Match score calculation

### 🎤 **Mock Interview Simulator**
- Practice behavioral, technical, and situational interviews
- AI feedback on answers and communication
- Body language and speech pattern analysis
- Progress tracking and improvement suggestions

### 💰 **Salary Insights**
- Real-time salary data by role and location
- Market trends and year-over-year growth
- Salary range comparisons
- Top companies and compensation data

### 🗺️ **Career Roadmap**
- Personalized step-by-step career guidance
- Task management and progress tracking
- Timeline-based milestone system
- Skills development recommendations

### 📧 **Email Automation**
- AI-generated personalized emails for recruiters
- Networking emails for mentors and professionals
- Email templates and customization
- Send tracking and analytics

## 🛠️ Tech Stack

- **Frontend**: React 19 + TypeScript
- **Styling**: Tailwind CSS
- **Routing**: React Router DOM
- **Icons**: Heroicons
- **Build Tool**: Vite
- **Package Manager**: npm

## 🚀 Getting Started

### Prerequisites
- Node.js (v18 or higher)
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MMU-hack/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to `http://localhost:5173`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 📁 Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable UI components
│   │   └── Navbar.tsx    # Navigation component
│   ├── pages/            # Main application pages
│   │   ├── HomePage.tsx
│   │   ├── ResumeBuilder.tsx
│   │   ├── JobMatcher.tsx
│   │   ├── MockInterview.tsx
│   │   ├── SalaryInsights.tsx
│   │   ├── Roadmap.tsx
│   │   └── EmailAutomation.tsx
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── services/         # API service functions (ready for backend)
│   ├── assets/           # Images and static files
│   ├── App.tsx           # Main application component
│   ├── main.tsx          # Application entry point
│   └── index.css         # Global styles and Tailwind imports
├── package.json
├── tailwind.config.js    # Tailwind CSS configuration
├── tsconfig.json         # TypeScript configuration
└── vite.config.ts        # Vite configuration
```

## 🎨 Design System

### Color Palette
- **Primary**: Blue shades (#3b82f6, #2563eb, #1d4ed8)
- **Success**: Green shades
- **Warning**: Yellow/Orange shades
- **Error**: Red shades
- **Neutral**: Gray shades

### Typography
- **Font**: System fonts (Inter, system-ui, Avenir, Helvetica, Arial, sans-serif)
- **Headings**: Semibold weight
- **Body**: Regular weight

### Components
- Consistent spacing using Tailwind's spacing scale
- Rounded corners for modern look
- Shadow system for depth
- Hover states and transitions for interactivity

## 🔧 Customization

### Adding New Pages
1. Create a new component in `src/pages/`
2. Add route in `App.tsx`
3. Add navigation link in `Navbar.tsx`

### Styling
- Use Tailwind CSS utility classes
- Custom styles can be added to `src/index.css`
- Component-specific styles using CSS modules if needed

### Types
- Add new TypeScript types in `src/types/index.ts`
- Use proper typing for all props and state

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

The build artifacts will be stored in the `dist/` directory.

### Deployment Options
- **Vercel**: Connect your GitHub repo for automatic deployments
- **Netlify**: Drag and drop the `dist/` folder
- **GitHub Pages**: Use GitHub Actions for automated deployment
- **AWS S3**: Upload to S3 bucket with CloudFront

## 🔜 Next Steps

### Backend Integration
- Set up API endpoints for all features
- Implement user authentication
- Connect to database for data persistence

### AI Services
- Integrate OpenAI API for resume suggestions
- Add speech-to-text for interview practice
- Implement NLP for job matching algorithms

### Enhanced Features
- File upload for resume parsing
- Calendar integration for interview scheduling
- Notification system
- Social sharing capabilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for university students everywhere**
