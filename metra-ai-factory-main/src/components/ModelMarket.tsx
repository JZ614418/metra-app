import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Wrench, Package } from 'lucide-react';

const ModelMarket = () => {
  const marketModels = [
    {
      id: '1',
      name: 'E-commerce Review Analyzer',
      description: 'Analyze customer reviews for sentiment and extract key issues',
      creator: 'DataPro Inc.',
      category: 'Text Analysis',
      price: '$49/month',
      rating: 4.8,
      downloads: 1250,
      tags: ['sentiment', 'e-commerce', 'NLP'],
      icon: '🛍️'
    },
    {
      id: '2',
      name: 'Medical Report Classifier',
      description: 'Classify medical reports and extract key medical terms',
      creator: 'HealthAI Lab',
      category: 'Healthcare',
      price: '$199/month',
      rating: 4.9,
      downloads: 432,
      tags: ['medical', 'classification', 'healthcare'],
      icon: '🏥'
    },
    {
      id: '3',
      name: 'Legal Document Analyzer',
      description: 'Extract key clauses and analyze legal documents',
      creator: 'LegalTech Pro',
      category: 'Legal',
      price: '$299/month',
      rating: 4.7,
      downloads: 289,
      tags: ['legal', 'document', 'analysis'],
      icon: '⚖️'
    }
  ];

  const categories = [
    'All Categories',
    'Text Analysis',
    'Image Recognition',
    'Healthcare',
    'Finance',
    'Legal',
    'Education',
    'Marketing'
  ];

  return (
    <div className="space-y-6">
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl">Model Marketplace</CardTitle>
          <p className="text-sm text-gray-500 mt-1">Discover and purchase pre-trained models</p>
        </CardHeader>
      </Card>

      <div className="h-64 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <Package className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Feature Under Development</h3>
          <p className="text-gray-600">Model marketplace feature is under development, stay tuned</p>
        </div>
      </div>
    </div>
  );
};

export default ModelMarket;
