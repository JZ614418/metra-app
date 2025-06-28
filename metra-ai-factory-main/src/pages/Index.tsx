import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Database, Brain, Cpu, Globe, Sparkles, Code, Upload, Bot, Zap, Target, BarChart, MessageSquare, User } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

const Index = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const coreModules = [
    {
      icon: MessageSquare,
      title: "Smart Dialogue",
      subtitle: "Natural Language",
      description: "Understand your needs through conversation and auto-generate data structures",
      features: ["Need Understanding", "Auto Planning", "Real-time Feedback", "Smart Optimization"]
    },
    {
      icon: Database,
      title: "Data Engine", 
      subtitle: "Multi-source",
      description: "Multi-source data collection, intelligent fusion, automatic quality detection",
      features: ["Web Scraping", "AI Generation", "File Upload", "Data Fusion"]
    },
    {
      icon: Brain,
      title: "Model Match",
      subtitle: "AI Recommendation", 
      description: "Intelligently recommend the best open-source model based on your task",
      features: ["Smart Matching", "Performance Compare", "Resource Evaluation", "One-click Select"]
    },
    {
      icon: Cpu,
      title: "Easy Training",
      subtitle: "No-code",
      description: "Hide all technical details, make training as simple as clicking a button",
      features: ["One-click Train", "Real-time Progress", "Auto Optimization", "Preview Results"]
    },
    {
      icon: Globe,
      title: "Instant Deploy",
      subtitle: "Ready to Use",
      description: "Use immediately after training, support API, plugins and more",
      features: ["API Interface", "Web Plugin", "Local Export", "Online Test"]
    }
  ];

  const demoExamples = [
    {
      title: "Customer Service Bot",
      icon: "💬",
      description: "Intelligent customer service model trained on company knowledge base",
      features: ["Q&A Support", "Emotion Detection", "Multi-turn Dialogue", "Knowledge Retrieval"],
      metric: "95% Accuracy",
      status: "Popular"
    },
    {
      title: "Content Creator",
      icon: "✍️", 
      description: "Content generation model trained on specific style",
      features: ["Style Imitation", "Creative Generation", "Multi-language", "Format Adaptation"],
      metric: "4.8/5 Satisfaction",
      status: "Creator's Choice"
    },
    {
      title: "Data Analyst",
      icon: "📊",
      description: "Analysis model trained on industry-specific data", 
      features: ["Trend Prediction", "Anomaly Detection", "Report Generation", "Visualization"],
      metric: "92% Accuracy", 
      status: "Enterprise Ready"
    }
  ];

  const userJourney = [
    { step: 1, title: "Describe Your Need", description: "Tell AI what you want", icon: MessageSquare },
    { step: 2, title: "Prepare Data", description: "AI helps collect and organize", icon: Database },
    { step: 3, title: "Select Model", description: "Smart recommendation", icon: Target },
    { step: 4, title: "Start Training", description: "One-click, auto optimize", icon: Zap },
    { step: 5, title: "Test Results", description: "Real-time preview", icon: BarChart },
    { step: 6, title: "Deploy & Use", description: "Multiple ways to integrate", icon: Globe }
  ];

  const advantages = [
    {
      icon: Sparkles,
      title: "Zero Barrier",
      description: "No coding or AI knowledge needed"
    },
    {
      icon: Zap,
      title: "Super Fast",
      description: "From idea to model in 1 hour"
    },
    {
      icon: Target,
      title: "High Accuracy",
      description: "Smart optimization for best results"
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">M</span>
              </div>
              <span className="font-semibold text-gray-900">Metra</span>
              <Badge variant="outline" className="text-xs">v4.0</Badge>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-600 hover:text-gray-900 text-sm">Features</a>
              <a href="#demos" className="text-gray-600 hover:text-gray-900 text-sm">Use Cases</a>
              <Link to="/pricing" className="text-gray-600 hover:text-gray-900 text-sm">Pricing</Link>
              <a href="#docs" className="text-gray-600 hover:text-gray-900 text-sm">Docs</a>
            </nav>
            <div className="flex items-center space-x-3">
              {user ? (
                <>
                  <Link to="/dashboard">
                    <Button variant="ghost" size="sm" className="flex items-center gap-2">
                      <User className="h-4 w-4" />
                      {user.full_name || user.email}
                    </Button>
                  </Link>
                  <Button variant="ghost" size="sm" onClick={handleLogout}>
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost" size="sm">Sign In</Button>
                  </Link>
                  <Link to="/register">
                    <Button size="sm" className="bg-gray-900 hover:bg-gray-800 text-white">
                      Get Started
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <div className="inline-flex items-center space-x-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="h-4 w-4" />
            <span>Train Your Own AI, No Code Required</span>
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Create Your Custom AI Model
            <br />
            <span className="text-gray-900">
              Through Natural Conversation
            </span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            No programming skills needed. Just tell Metra what you want,
            and we'll handle everything from data to deployment.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link to="/dashboard">
              <Button size="lg" className="bg-gray-900 hover:bg-gray-800 text-white">
                Start Building
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Button variant="outline" size="lg">
              Watch Demo
            </Button>
          </div>
          <div className="flex items-center justify-center space-x-8 text-sm text-gray-500">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>5-min Setup</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Expert Support</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Flexible Pricing</span>
            </div>
          </div>
        </div>
      </section>

      {/* Advantages */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {advantages.map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-12 h-12 bg-gray-200 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <item.icon className="h-6 w-6 text-gray-700" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-gray-600">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* User Journey */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Incredibly Simple Workflow</h2>
            <p className="text-lg text-gray-600">Six steps from idea to working AI model</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {userJourney.map((item, index) => (
              <div key={index} className="relative">
                <div className="flex flex-col items-center text-center p-6">
                  <div className="w-12 h-12 bg-gray-200 rounded-xl flex items-center justify-center mb-4">
                    <item.icon className="h-6 w-6 text-gray-700" />
                  </div>
                  <div className="w-8 h-8 bg-gray-900 rounded-full flex items-center justify-center mb-3">
                    <span className="text-white text-sm font-bold">{item.step}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{item.title}</h3>
                  <p className="text-gray-600 text-sm">{item.description}</p>
                </div>
                {index < userJourney.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-3 transform -translate-y-1/2">
                    <ArrowRight className="h-5 w-5 text-gray-300" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Core Features */}
      <section id="features" className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Built for Non-Technical Users</h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Every feature is carefully designed to ensure anyone can use it
          </p>
        </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {coreModules.map((module, index) => (
              <Card key={index} className="border-0 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1">
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                    <div className="w-12 h-12 bg-gray-200 rounded-xl flex items-center justify-center flex-shrink-0">
                    <module.icon className="h-6 w-6 text-gray-700" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{module.title}</h3>
                        <Badge variant="outline" className="text-xs">
                          {module.subtitle}
                        </Badge>
                    </div>
                    <p className="text-gray-600 text-sm mb-3 leading-relaxed">{module.description}</p>
                    <div className="grid grid-cols-2 gap-2">
                      {module.features.map((feature, featureIndex) => (
                        <div key={featureIndex} className="flex items-center space-x-2">
                          <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                          <span className="text-xs text-gray-600">{feature}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          </div>
        </div>
      </section>

      {/* Demo Examples */}
      <section id="demos" className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">See What Others Are Building</h2>
            <p className="text-lg text-gray-600">Users from all industries are creating custom AI with Metra</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {demoExamples.map((demo, index) => (
              <Card key={index} className="border-0 shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1">
                <CardContent className="p-6">
                  <div className="text-center mb-4">
                    <div className="text-4xl mb-3">{demo.icon}</div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{demo.title}</h3>
                    <Badge className='bg-gray-100 text-gray-800'>
                      {demo.status}
                    </Badge>
                  </div>
                  <p className="text-gray-600 text-sm mb-4 leading-relaxed">{demo.description}</p>
                  <div className="space-y-2 mb-4">
                    {demo.features.map((feature, featureIndex) => (
                      <div key={featureIndex} className="flex items-center space-x-2">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>
                        <span className="text-xs text-gray-600">{feature}</span>
                      </div>
                    ))}
                  </div>
                  <div className="pt-3 border-t border-gray-100">
                    <div className="text-xs text-gray-500 mb-1">Performance</div>
                    <div className="text-sm font-medium text-gray-900">{demo.metric}</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <Card className="border-0 shadow-lg bg-gray-900 text-white overflow-hidden relative">
          <div className="absolute inset-0 bg-black opacity-10"></div>
          <CardContent className="p-12 text-center relative z-10">
            <h2 className="text-3xl font-bold mb-4">Ready to Create Your Custom AI?</h2>
            <p className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto">
              Join thousands of creators, entrepreneurs, and professionals making AI work for them
            </p>
            <Link to="/dashboard">
              <Button size="lg" className="bg-white text-gray-900 hover:bg-gray-100">
                Start Now
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <p className="text-sm text-gray-400 mt-4">Multiple pricing plans · Expert support · Enterprise ready</p>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Product</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="#" className="hover:text-gray-900">Features</a></li>
                <li><a href="#" className="hover:text-gray-900">Use Cases</a></li>
                <li><Link to="/pricing" className="hover:text-gray-900">Pricing</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Resources</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="#" className="hover:text-gray-900">Help Center</a></li>
                <li><a href="#" className="hover:text-gray-900">Video Tutorials</a></li>
                <li><a href="#" className="hover:text-gray-900">Best Practices</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Developers</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="#" className="hover:text-gray-900">API Docs</a></li>
                <li><a href="#" className="hover:text-gray-900">Integration Guide</a></li>
                <li><a href="#" className="hover:text-gray-900">Open Source</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Company</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="#" className="hover:text-gray-900">About</a></li>
                <li><a href="#" className="hover:text-gray-900">Blog</a></li>
                <li><a href="#" className="hover:text-gray-900">Contact</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-200 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-6 h-6 bg-gray-900 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xs">M</span>
              </div>
              <span className="text-sm text-gray-600">© 2024 Metra. All rights reserved.</span>
            </div>
            <div className="flex space-x-6 text-sm text-gray-600">
              <a href="#" className="hover:text-gray-900">Privacy Policy</a>
              <a href="#" className="hover:text-gray-900">Terms of Service</a>
              <a href="#" className="hover:text-gray-900">Cookie Settings</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
