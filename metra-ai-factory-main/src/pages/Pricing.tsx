import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Check, Star, Zap, Crown, Database, Cpu, Globe, Download, X, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

const Pricing = () => {
  const plans = [
    {
      name: 'Starter',
      price: '$0',
      period: 'forever',
      description: 'Perfect for trying out Metra',
      icon: Star,
      features: [
        { text: '3 models per month', included: true },
        { text: '1,000 API calls per month', included: true },
        { text: 'Basic models only', included: true },
        { text: 'Community support', included: true },
        { text: 'Model export', included: false },
        { text: 'Custom deployment', included: false },
        { text: 'Priority support', included: false },
        { text: 'Advanced analytics', included: false }
      ],
      limitations: [
        "Limited data processing",
        "Limited GPU training hours",
        "Limited API calls"
      ],
      buttonText: 'Start Free',
      buttonVariant: 'outline' as const,
      popular: false
    },
    {
      name: 'Professional',
      price: '$49',
      period: 'per month',
      description: 'For professionals and small teams',
      icon: Zap,
      features: [
        { text: '20 models per month', included: true },
        { text: '50,000 API calls per month', included: true },
        { text: 'All model types', included: true },
        { text: 'Email support', included: true },
        { text: 'Model export', included: true },
        { text: 'Custom deployment', included: true },
        { text: 'Priority support', included: false },
        { text: 'Advanced analytics', included: false }
      ],
      limitations: [],
      buttonText: 'Start Trial',
      buttonVariant: 'default' as const,
      popular: true,
      badge: 'Most Popular'
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: 'contact sales',
      description: 'For large teams and organizations',
      icon: Crown,
      features: [
        { text: 'Unlimited models', included: true },
        { text: 'Unlimited API calls', included: true },
        { text: 'All model types', included: true },
        { text: 'Dedicated support', included: true },
        { text: 'Model export', included: true },
        { text: 'Custom deployment', included: true },
        { text: 'Priority support', included: true },
        { text: 'Advanced analytics', included: true }
      ],
      limitations: [],
      buttonText: 'Contact Sales',
      buttonVariant: 'outline' as const,
      popular: false
    }
  ];

  const pricingModules = [
    {
      icon: Database,
      name: "Data Processing",
      description: "Pay per data volume",
      pricing: [
        { plan: "Free", price: "Free", limit: "1K samples" },
        { plan: "Pro", price: "$0.001/sample", limit: "500K samples" },
        { plan: "Enterprise", price: "Custom", limit: "Unlimited" }
      ]
    },
    {
      icon: Cpu,
      name: "Model Training", 
      description: "Pay per GPU hour",
      pricing: [
        { plan: "Free", price: "Free", limit: "2 hours" },
        { plan: "Pro", price: "$0.6/hour", limit: "100 hours" },
        { plan: "Enterprise", price: "$0.45/hour", limit: "500 hours" }
      ]
    },
    {
      icon: Globe,
      name: "API Usage",
      description: "Pay per request", 
      pricing: [
        { plan: "Free", price: "Free", limit: "1K/month" },
        { plan: "Pro", price: "$0.0003/call", limit: "100K/month" },
        { plan: "Enterprise", price: "$0.0002/call", limit: "Unlimited" }
      ]
    },
    {
      icon: Download,
      name: "Model Export",
      description: "One-time purchase",
      pricing: [
        { plan: "Personal", price: "$9.99", limit: "Single model" },
        { plan: "Commercial", price: "$49.99", limit: "Commercial license" },
        { plan: "Source Code", price: "$149.99", limit: "Full source code" }
      ]
    }
  ];

  const faqs = [
    {
      question: "Can I change plans anytime?",
      answer: "Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately."
    },
    {
      question: "What payment methods do you accept?",
      answer: "We accept all major credit cards, debit cards, and PayPal. Enterprise customers can pay by invoice."
    },
    {
      question: "Is there a free trial?",
      answer: "Yes, Professional and Enterprise plans come with a 14-day free trial. No credit card required."
    },
    {
      question: "What happens if I exceed my limits?",
      answer: "We'll notify you when you're close to your limits. You can upgrade your plan or purchase additional resources as needed."
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">M</span>
              </div>
              <span className="font-semibold text-gray-900">Metra</span>
            </Link>
            <nav className="flex items-center space-x-8">
              <Link to="/" className="text-gray-600 hover:text-gray-900 text-sm">Home</Link>
              <Link to="/dashboard" className="text-gray-600 hover:text-gray-900 text-sm">Dashboard</Link>
              <Button size="sm" className="bg-gray-900 hover:bg-gray-800 text-white">
                Get Started
              </Button>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
            Choose the plan that fits your needs. All plans include core features.
            Upgrade or downgrade anytime.
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section id="pricing" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <Card 
              key={index} 
              className={`relative ${
                plan.popular 
                  ? 'border-2 border-gray-900 shadow-xl' 
                  : 'border border-gray-200'
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-gray-900 text-white px-3 py-1">
                    <Sparkles className="h-3 w-3 mr-1" />
                    {plan.badge}
                  </Badge>
                </div>
              )}
              <CardHeader className="text-center pb-8">
                <div className="w-12 h-12 mx-auto mb-4 bg-gray-100 rounded-xl flex items-center justify-center">
                  <plan.icon className="h-6 w-6 text-gray-700" />
                </div>
                <CardTitle className="text-2xl font-bold text-gray-900 mb-2">
                  {plan.name}
                </CardTitle>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                  <span className="text-gray-600 text-sm ml-1">/{plan.period}</span>
                </div>
                <p className="text-gray-600">{plan.description}</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-3">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start space-x-3">
                      {feature.included ? (
                        <Check className="h-5 w-5 text-green-600 mt-0.5" />
                      ) : (
                        <X className="h-5 w-5 text-gray-400 mt-0.5" />
                      )}
                      <span className={`text-sm ${
                        feature.included ? 'text-gray-900' : 'text-gray-400'
                      }`}>
                        {feature.text}
                      </span>
                    </li>
                      ))}
                </ul>
                    <Button 
                  className={`w-full ${
                    plan.popular 
                      ? 'bg-gray-900 hover:bg-gray-800 text-white' 
                      : 'bg-white hover:bg-gray-50 text-gray-900 border border-gray-300'
                  }`}
                      >
                        {plan.buttonText}
                      </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Pricing Modules */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Pay As You Go</h2>
            <p className="text-lg text-gray-600">Flexible pricing for each module</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {pricingModules.map((module, index) => (
              <Card key={index} className="border-0 shadow-sm">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <module.icon className="h-6 w-6 text-gray-700" />
                    <div>
                      <CardTitle className="text-lg">{module.name}</CardTitle>
                      <p className="text-sm text-gray-600">{module.description}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {module.pricing.map((item, itemIndex) => (
                      <div key={itemIndex} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <div>
                          <div className="font-medium text-sm">{item.plan}</div>
                          <div className="text-xs text-gray-500">{item.limit}</div>
                        </div>
                        <div className="font-semibold text-gray-900">{item.price}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h2>
          <p className="text-lg text-gray-600">Everything you need to know about our pricing</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {faqs.map((faq, index) => (
            <Card key={index} className="border-0 shadow-sm">
              <CardContent className="p-6">
                <h3 className="font-semibold text-gray-900 mb-3">{faq.question}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{faq.answer}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <Card className="border-0 shadow-sm bg-gray-900 text-white">
          <CardContent className="p-12 text-center">
            <h2 className="text-3xl font-bold mb-4">Still have questions?</h2>
            <p className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto">
              Our technical team is ready to provide professional AI training consultation
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary" className="bg-white text-gray-900 hover:bg-gray-100">
                Contact Support
              </Button>
              <Button size="lg" variant="secondary" className="bg-white text-gray-900 hover:bg-gray-100">
                Schedule Demo
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
};

export default Pricing;
