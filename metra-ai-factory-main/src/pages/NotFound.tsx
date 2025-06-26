import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

const NotFound = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-gray-200">404</h1>
          <div className="mt-4">
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Page Not Found
            </h2>
            <p className="text-gray-600">
              Sorry, the page you're looking for doesn't exist or has been moved.
            </p>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/">
            <Button variant="outline" className="w-full sm:w-auto">
              <Home className="mr-2 h-4 w-4" />
              Back to Home
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button className="w-full sm:w-auto bg-gray-900 hover:bg-gray-800">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Go to Dashboard
            </Button>
          </Link>
        </div>
        
        <div className="mt-8 text-sm text-gray-500">
          Need help? <a href="#" className="text-gray-900 hover:underline">Contact Support</a>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
