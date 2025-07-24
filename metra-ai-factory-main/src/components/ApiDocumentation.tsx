import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Copy, Code, Book, Zap, Shield, AlertTriangle, 
  ExternalLink, CheckCircle2, DollarSign, Settings,
  Terminal, Globe, Key, FileText
} from 'lucide-react';
import { toast } from 'sonner';

interface ApiDocumentationProps {
  documentation: any;
  endpoint: string;
  modelVersion: string;
}

const ApiDocumentation: React.FC<ApiDocumentationProps> = ({ 
  documentation, 
  endpoint, 
  modelVersion 
}) => {
  const [selectedLanguage, setSelectedLanguage] = useState('curl');

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const languages = [
    { key: 'curl', name: 'cURL', icon: Terminal },
    { key: 'python', name: 'Python SDK', icon: Code },
    { key: 'python_requests', name: 'Python Requests', icon: Code },
    { key: 'javascript', name: 'JavaScript', icon: Globe }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Book className="h-5 w-5" />
            API Documentation
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            {documentation.description}
          </p>
        </div>
        <Badge variant="outline" className="font-mono text-xs">
          {modelVersion?.slice(0, 12)}...
        </Badge>
      </div>

      <Tabs defaultValue="quickstart" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="quickstart">Quick Start</TabsTrigger>
          <TabsTrigger value="examples">Code Examples</TabsTrigger>
          <TabsTrigger value="reference">API Reference</TabsTrigger>
          <TabsTrigger value="pricing">Pricing</TabsTrigger>
          <TabsTrigger value="troubleshooting">Help</TabsTrigger>
        </TabsList>

        {/* Quick Start Tab */}
        <TabsContent value="quickstart" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Setup Guide
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {documentation.setup_guide?.map((step: any, index: number) => (
                <div key={index} className="flex gap-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                    {step.step}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-sm">{step.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded mt-2 inline-block">
                      {step.action}
                    </code>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Quick Example */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Terminal className="h-4 w-4" />
                Quick Test
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm">
                <pre className="whitespace-pre-wrap">
                  {documentation.code_examples?.curl}
                </pre>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="mt-3"
                onClick={() => copyToClipboard(documentation.code_examples?.curl || '')}
              >
                <Copy className="h-3 w-3 mr-1" />
                Copy cURL Command
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Code Examples Tab */}
        <TabsContent value="examples" className="space-y-4">
          <div className="flex gap-2 mb-4">
            {languages.map((lang) => {
              const Icon = lang.icon;
              return (
                <Button
                  key={lang.key}
                  size="sm"
                  variant={selectedLanguage === lang.key ? "default" : "outline"}
                  onClick={() => setSelectedLanguage(lang.key)}
                  className="flex items-center gap-2"
                >
                  <Icon className="h-3 w-3" />
                  {lang.name}
                </Button>
              );
            })}
          </div>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm">
                {languages.find(l => l.key === selectedLanguage)?.name} Example
              </CardTitle>
              <Button
                size="sm"
                variant="outline"
                onClick={() => copyToClipboard(documentation.code_examples?.[selectedLanguage] || '')}
              >
                <Copy className="h-3 w-3 mr-1" />
                Copy
              </Button>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm">
                  <pre className="whitespace-pre-wrap">
                    {documentation.code_examples?.[selectedLanguage]}
                  </pre>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Best Practices */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Best Practices
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {documentation.best_practices?.map((practice: string, index: number) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span>{practice}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Reference Tab */}
        <TabsContent value="reference" className="space-y-4">
          {/* Authentication */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Authentication
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <span className="text-sm font-medium">Type:</span>
                <Badge variant="outline" className="ml-2">
                  {documentation.authentication?.type}
                </Badge>
              </div>
              <div>
                <span className="text-sm font-medium">Header:</span>
                <code className="ml-2 px-2 py-1 bg-gray-100 rounded text-xs">
                  {documentation.authentication?.header}
                </code>
              </div>
              <div>
                <span className="text-sm font-medium">Get Token:</span>
                <a 
                  href={documentation.authentication?.get_token}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1 inline-flex"
                >
                  Replicate Account
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </CardContent>
          </Card>

          {/* Request Format */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Request Format
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-50 p-3 rounded-lg">
                <pre className="text-sm whitespace-pre-wrap">
                  {JSON.stringify(documentation.request_format, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>

          {/* Response Format */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Response Format
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-50 p-3 rounded-lg">
                <pre className="text-sm whitespace-pre-wrap">
                  {JSON.stringify(documentation.response_format, null, 2)}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Pricing Tab */}
        <TabsContent value="pricing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Pricing Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm font-medium text-gray-600">Model:</span>
                  <p className="font-medium">{documentation.pricing?.model}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-600">Cost Range:</span>
                  <p className="font-medium text-green-600">{documentation.pricing?.cost_range}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-600">Billing:</span>
                  <p className="font-medium">{documentation.pricing?.billing}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-600">Details:</span>
                  <p className="text-sm text-gray-600">{documentation.pricing?.details}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Troubleshooting Tab */}
        <TabsContent value="troubleshooting" className="space-y-4">
          {/* Common Errors */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Common Errors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(documentation.troubleshooting?.common_errors || {}).map(([error, solution]) => (
                  <div key={error} className="border-l-4 border-red-200 pl-4">
                    <h4 className="font-medium text-sm text-red-800">{error}</h4>
                    <p className="text-sm text-gray-600 mt-1">{solution as string}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Support Resources */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Support Resources
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-3">
                {Object.entries(documentation.troubleshooting?.support || {}).map(([type, url]) => (
                  <a 
                    key={type}
                    href={url as string}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <ExternalLink className="h-4 w-4 text-gray-500" />
                    <div>
                      <div className="font-medium text-sm capitalize">{type}</div>
                      <div className="text-xs text-gray-500">{url as string}</div>
                    </div>
                  </a>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ApiDocumentation;